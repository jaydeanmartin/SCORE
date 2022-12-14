# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.


from locomotives.models import Consist, Route, Policy, LTDResults, ConsistCar, Segment, Session
from locomotives.serializers import ConsistSerializer, Route2Serializer
from locomotives.ltd import MPH2MPS, get_segments
from locomotives.views import get_visible
from locomotives.consist_data import get_consist_data

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view, renderer_classes, permission_classes

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from .tasks import eval_ltd
from celery.result import AsyncResult

KW2HP = 1.34102     # convert kw to hp
TONNE2TON = 1.10231 # convert tonne (1000 kg) to ton (2000 lbs)
MPH2MPS = 0.44704   # convert MPH to m/s
MI2M = 1609.34      # convert mile to meter

class ConsistList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Consist.objects.all()
    serializer_class = ConsistSerializer

class ConsistDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Consist.objects.all()
    serializer_class = ConsistSerializer

class RouteList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Route.objects.all()
    serializer_class = Route2Serializer

class RouteDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Route.objects.all()
    serializer_class = Route2Serializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def evaluate(request):
    data = request.data
    # print('data: ', request.data)
    route_id = data.getlist('routes', [27])[0]
    consist_id = data.getlist('consists', [16])[0]
    policy_type = data.get('policy_type', ['user_fixed'])
    power_order = data.getlist('power_order[]')
    braking = data.get('braking', ['maximum_braking'])
    max_speed = float(data.get('max_speed', 60)) * MPH2MPS
    session_id = data.get('session_id', 0)
    if session_id != 0:
        session = Session.objects.get(id=session_id)
    else:
        session = None

    if data.get('rapid', 'true') == "true":
        rapid = True
    else:
        rapid = False

    r = Route.objects.get(id=route_id)
    c = Consist.objects.get(id=consist_id)
    # we can change the max speed later on in the interface
    p, created = Policy.objects.get_or_create(type=policy_type, power_order=power_order, braking=braking, max_speed=max_speed)
    
    print("about to get an LTDResults object with session: ", session)

    result, created = LTDResults.objects.get_or_create(
       route = r,
       consist = c,
       policy = p,
       rapid = rapid,
       session = session
    )

    # temporarily force the evaluation till things are working properly
    result.status = 0
    result.result_code = -1
    result.save()

    task = eval_ltd.delay(result.id)

    print("new LTDResult: ", created, result.id)

    # return JsonResponse({'result_id': result.id}, status=202)
    return JsonResponse({'result_id': result.id}, status=202)

def home(request):
    return render(request, 'api_home.html')

def task_status(request, task_id):
    task = AsyncResult(task_id)

    if task.state == 'FAILURE' or task.status == 'PENDING':
        response = {
            'task_id': task_id,
            'state': task.state,
            'progression': "None",
            'info':str(task.info)
        }
        return JsonResponse(response, status=200)
    current = task.info.get('current', 0)
    total = task.info.get('total', 1)
    progression = (int(current) / int(total)) * 100 # to display a percentage of progression
    response = {
        'task_id': task_id,
        'state': task.state,
        'progression': progression,
        'info': task.info.get('result_id', "None")
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ltd_status(request, result_id):
    result = LTDResults.objects.get(id = result_id)
    response = {
        'result_id': result.id,
        'state': result.result_code,
        'progression': result.status,
        'route': result.route.name,
        'consist': result.consist.name,
        'policy': result.policy.name(),
        'max_speed': round(result.policy.max_speed/MPH2MPS),  # convert back to MPH
        'rapid': result.rapid,
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ltd_result(request, result_id):
    result = LTDResults.objects.get(id = result_id)
    response = {
        'route': {
            'name': result.route.name,
            'id' : result.route.id
        },
        'consist': {
            'name' : result.consist.name,
            'id' : result.consist.id
        },
        'policy': result.policy.name(),
        'max_speed': result.policy.max_speed/MPH2MPS,
        'rapid': result.rapid,
        'data': result.result,
        'superuser': request.user.is_superuser,
    }
    return JsonResponse(response, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_info(request, pk):
    consist = Consist.objects.get(id = pk)
    consist_info = get_consist_data(consist)
    return JsonResponse(consist_info, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_elevation(request, pk):
    route = Route.objects.get(id=pk)
    segments = Segment.objects.filter(route=route).order_by('segment_order').all()
    route_dist_seg = 0
    elevation_data = []
    for i, seg in enumerate(segments):
        route_dist_seg += seg.arc_distance
        elevation_data.append([route_dist_seg, seg.locations.all()[1].smooth_elev_m])
    elevation_lines = { 'data': elevation_data}
    return JsonResponse(elevation_lines, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_list(request):
    route_info = {}
    routes = get_visible(request.user, Route.objects.all())
    for route in routes:
        route_info[route.id] = route.name

    return JsonResponse(route_info, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_route_data(request, pk):
    route = Route.objects.get(id=pk)
    route_data = get_segments(route)
    return JsonResponse(route_data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_list(request):
    consist_info = {}

    consists = get_visible(request.user, Consist.objects.filter(most_recent_version=True))
    for consist in consists:
        consist_info[consist.id] = consist.name

    return JsonResponse(consist_info, status=200)

def get_locomotive_type(consist):
    consist_locomotive_types = []
    consist_list = ConsistCar.objects.filter(consist=consist)
    for car in consist_list:
        if car.car.type == 'D':
            consist_locomotive_types.append('diesel')
        if car.car.type == 'E':
            consist_locomotive_types.append('battery')
        if car.car.type == 'C':
            consist_locomotive_types.append('fuelcell')
    return consist_locomotive_types

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consist_powers(request, pk):

    consist = Consist.objects.get(id=pk)
    results = {'data': get_locomotive_type(consist)}

    return JsonResponse(results, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ltd_summary(request, result_id):
    # this function will return a dictionary of values for a design in the tradespace
    # it will only return values if the analysis has completed successfully
    # print('checking result: ' + result_id)
    result = LTDResults.objects.get(id = result_id)
    data = {}
    data['status'] = result.result_code
    if result.result_code == 0:
        # we have a completed ltd analysis get the stored out put from the analysis
        output = result.result
        data['duration_hrs'] = output['duration']/3600      # convert from seconds to hrs
        perfs = output['perfs']
        consist_info = get_consist_data(result.consist)
        data['diesel_consumed_kg'] = perfs['fuel_diesel'][-1]
        data['hydrogen_consumed_kg'] = perfs['fuel_hydrogen'][-1]
        data['energy_cost'] = perfs['fuel_cost']
        data['cost_per_ton_mile'] = perfs['fuel_cost']/(consist_info['freight_tons']*output['distances'][-1]/MI2M)
        data['max_speed_mph'] = result.policy.max_speed/MPH2MPS
        data['route_id'] = result.route.id
        data['route_name'] = result.route.name
        data['consist_id'] = result.consist.id
        data['consist_name'] = result.consist.name
        s = "automatic"
        if result.policy.type == 'user_fixed':
            str = ""
            for p in result.policy.power_order:
                if p is not None:
                    str += p + ", "
            s = str[:-2]
        data['power_order'] = s
        data['braking'] = result.policy.braking
        data['total_weight_tons'] = consist_info['weight_tons']
        data['number_of_cars'] = consist_info['number_cars']
        data['trailing_weight_tons'] =  consist_info['trailing_tons']
        data['max_power_hp'] = consist_info['power_hp']
        data['max_battery_energy_kw-hr'] = consist_info['battery_energy']
    return JsonResponse(data, status=200)
