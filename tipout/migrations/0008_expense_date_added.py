# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-01 19:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tipout', '0007_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='date_added',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
