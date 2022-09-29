# Generated by Django 4.0.4 on 2022-07-18 22:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0031_locomotivemodel_tier_lar_emissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Emission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('power_level', models.CharField(choices=[('N5', 'notch 5'), ('N6', 'notch 6'), ('N1', 'notch 1'), ('N8', 'notch 8'), ('LI', 'idle'), ('N7', 'notch 7'), ('N2', 'notch 2'), ('DB', 'dynamic brake'), ('N3', 'notch 3'), ('N4', 'notch 4')], max_length=20)),
                ('power', models.FloatField(blank=True, null=True)),
                ('fuel_consumption', models.FloatField(blank=True, null=True)),
                ('ghg_hc_emissions', models.FloatField(blank=True, null=True)),
                ('ghg_co_emissions', models.FloatField(blank=True, null=True)),
                ('ghg_no_emissions', models.FloatField(blank=True, null=True)),
                ('ghg_pm_emissions', models.FloatField(blank=True, null=True)),
                ('ghg_co2_emissions', models.FloatField(blank=True, null=True)),
                ('LAR', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='locomotives.lar')),
            ],
        ),
        migrations.DeleteModel(
            name='emissions',
        ),
    ]