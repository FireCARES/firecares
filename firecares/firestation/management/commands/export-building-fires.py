from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment


class Command(BaseCommand):
    """
    This command is used to export data that department heat maps visualize.
    """

    help = 'Creates a sql file to export building fires from.'

    def handle(self, *args, **options):
        vals = FireDepartment.objects.filter(fdid__isnull=False, state__isnull=False).exclude(fdid__exact='').values_list('id', 'state', 'fdid')

        sql = """
COPY (
    SELECT alarm, a.inc_type, alarms, ff_death, oth_death, ST_X(geom) as x, ST_Y(geom) as y, COALESCE(y.risk_category, 'Unknown') as risk_category
    FROM buildingfires a
    LEFT JOIN (
        SELECT state, fdid, inc_date, inc_no, exp_no, x.geom, x.parcel_id, x.risk_category
        FROM (
            SELECT * FROM joint_incidentaddress j
            LEFT JOIN parcel_risk_category_local using (parcel_id)
            WHERE j.state = '{state}' AND j.fdid = '{fdid}'
        ) AS x
    ) AS y
    USING (state, fdid, inc_date, inc_no, exp_no)
    WHERE a.state = '{state}' and a.fdid = '{fdid}'
) TO PROGRAM 'aws s3 cp - s3://firecares-test/{id}-building-fires.csv --acl="public-read"'  DELIMITER ',' CSV HEADER;

"""

        for fd in vals:
            self.stdout.write(sql.format(fdid=fd[2], state=fd[1], id=fd[0]))
