# Generated by Django 3.1.4 on 2022-02-17 20:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0011_policy'),
    ]

    operations = [
        migrations.AddField(
            model_name='consistrouteevaluation',
            name='policy',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='locomotives.policy'),
        ),
    ]
