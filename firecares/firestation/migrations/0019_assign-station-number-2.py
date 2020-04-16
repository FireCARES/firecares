# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0018_assign_station_number'),
    ]

    sql = """
BEGIN TRANSACTION;

-- If postgres supported negative lookbehind regexes, this'd be a little simpler
SELECT src.id, array_to_string(regexp_matches(src.newname, '(\d+)'), ',') as num, src.name
INTO TEMP tmp_fs
FROM (
	SELECT sd.id, regexp_replace(sd.name, 'Battalion\s+\d+', '') as newname, sd.name
	FROM firestation_firestation fs
	INNER JOIN firestation_usgsstructuredata sd on sd.id = fs.usgsstructuredata_ptr_id
	WHERE sd.name ~ '.*\d+.*'
		AND fs.station_number is null
) AS src;

UPDATE firestation_firestation
SET station_number = cast(tmp_fs.num as int)
FROM tmp_fs
WHERE tmp_fs.id = usgsstructuredata_ptr_id;

DROP TABLE tmp_fs;

COMMIT;
"""

    operations = [
        migrations.RunSQL(sql),
    ]
