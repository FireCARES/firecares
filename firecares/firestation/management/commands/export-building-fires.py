from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment


class Command(BaseCommand):
    """
    This command is used to export data that department heat maps visualize.
    """

    help = 'Creates a sql file to export building fires from.'

    def handle(self, *args, **options):
        vals = FireDepartment.objects.filter(fdid__isnull=False, state__isnull=False).exclude(fdid__exact='')

        sql = """
       \COPY (select alarm, a.inc_type, alarms,ff_death, oth_death, ST_X(geom) as x, st_y(geom) as y  from buildingfires a left join incidentaddress b using (state, inc_date, exp_no, fdid, inc_no) where state='{state}' and fdid='{fdid}') to PROGRAM 'aws s3 cp - s3://firecares-pipeline/heatmaps/{id}-building-fires.csv --acl=\"public-read\"' DELIMITER ',' CSV HEADER;
        """

        for fd in vals:
            self.stdout.write(sql.format(fdid=fd.fdid, state=fd.state, id=fd.id) + '\n')