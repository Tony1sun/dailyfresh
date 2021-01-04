# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booktest', '0002_heroinfo_isdelete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heroinfo',
            name='hcomment',
            field=models.CharField(blank=True, null=True, max_length=200),
        ),
    ]