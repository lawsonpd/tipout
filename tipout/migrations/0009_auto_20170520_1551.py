# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-20 15:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tipout', '0008_auto_20170520_1313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otherfunds',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otherfunds', to='tipout.Employee'),
        ),
    ]