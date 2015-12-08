# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0017_auto_20151006_1453'),
    ]

    sql = """
BEGIN TRANSACTION;

SELECT sd.id, array_to_string(regexp_matches(name, 'Station\s(\d+)'),',') as num
INTO TEMP tmp_fs
FROM firestation_firestation fs
INNER JOIN firestation_usgsstructuredata sd on sd.id = fs.usgsstructuredata_ptr_id
WHERE name ~ 'Station\s\d+';

UPDATE firestation_firestation
SET station_number = cast(tmp_fs.num as int)
FROM tmp_fs
WHERE tmp_fs.id = usgsstructuredata_ptr_id;

DROP TABLE tmp_fs;

COMMIT;
    """

    # All firestations had a null station_number to begin with
    reverse_sql = """
UPDATE firestation_firestation
SET station_number = null;
    """

    operations = [
        migrations.RunSQL(sql, reverse_sql=reverse_sql),
    ]
