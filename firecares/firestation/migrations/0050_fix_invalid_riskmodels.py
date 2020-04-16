# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0049_auto_20170320_1017'),
    ]

    sql = """
delete from firestation_firedepartmentriskmodels
where id in
    (select rows.id from
        (select row_number() over (partition by rm.department_id, rm.level) as num, rm.level, rm.department_id, rm.id
        from firestation_firedepartmentriskmodels rm
        inner join
            (select department_id, level
            from firestation_firedepartmentriskmodels
            group by department_id, level having count(1) > 1) as q
        using (level, department_id)
    ) as rows
where rows.num > 1)
"""

    operations = [
        migrations.RunSQL(sql)
    ]
