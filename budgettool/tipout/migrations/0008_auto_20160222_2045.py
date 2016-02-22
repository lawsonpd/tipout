# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-22 20:45
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tipout', '0007_auto_20160222_0556'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expenditure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost', models.IntegerField()),
                ('date', models.DateField(default=datetime.date.today)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenditures', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='dailyexpenditures',
            name='owner',
        ),
        migrations.DeleteModel(
            name='DailyExpenditures',
        ),
    ]
