# Generated by Django 3.1.4 on 2021-12-09 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locomotives', '0003_auto_20211209_1544'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electriclocomotive',
            name='power_in',
            field=models.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name='electriclocomotive',
            name='power_out',
            field=models.JSONField(null=True),
        ),
    ]
