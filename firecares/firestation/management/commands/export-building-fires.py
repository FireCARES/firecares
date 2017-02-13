from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment


class Command(BaseCommand):
    """
    This command is used to export data that department heat maps visualize.
    """

    help = 'Creates a sql file to export building fires from.'

    def handle(self, *args, **options):
        vals = FireDepartment.objects.filter(fdid__isnull=False, state__isnull=False).exclude(fdid__exact='')

        sql = """\COPY (select alarm, a.inc_type, alarms,ff_death, oth_death, ST_X(geom) as x, st_y(geom) as y, COALESCE(b.risk_category, 'Unknown') as risk_category from buildingfires a left join (SELECT * FROM (SELECT state, fdid, inc_date, inc_no, exp_no, geom, b.parcel_id, b.risk_category, ROW_NUMBER() OVER (PARTITION BY state, fdid, inc_date, inc_no, exp_no, geom ORDER BY st_distance(st_centroid(b.wkb_geometry), a.geom)) AS r FROM (select * from incidentaddress where state='{state}' and fdid='{fdid}') a left join parcel_risk_category_local b on a.geom && b.wkb_geometry) x WHERE x.r = 1) b using (state, inc_date, exp_no, fdid, inc_no) where state='{state}' and fdid='{fdid}') to PROGRAM 'aws s3 cp - s3://firecares-test/{id}-building-fires.csv --acl="public-read"' DELIMITER ',' CSV HEADER;"""

        for fd in vals:
            self.stdout.write(sql.format(fdid=fd.fdid, state=fd.state, id=fd.id) + '\n\n')
