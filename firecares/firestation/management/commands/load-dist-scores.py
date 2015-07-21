from fire_risk.models import DIST
from fire_risk.models.DIST.providers.ahs import ahs_building_areas
from fire_risk.backends import PostgresBackend
from fire_risk.backends.queries import RESIDENTIAL_FIRES_BY_FDID_STATE
from firecares.firestation.models import FireDepartment
from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    help = 'Updates the DIST score for a department'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry-run',
                    dest='dry_run',
                    default=False,
                    help='If specified the Fire Department records will not updated.'),
    )

    def handle(self, *args, **options):
        vals = FireDepartment.objects.filter(dist_model_score__isnull=True)

        dists = []

        with PostgresBackend(dict(host='localhost')) as backend:
            for fd in vals:
                results = backend.get_firespread_counts(query=RESIDENTIAL_FIRES_BY_FDID_STATE, query_params=(fd.fdid, fd.state))
                ahs_building_size = ahs_building_areas(fd.fdid, fd.state)

                if ahs_building_size is not None:
                    results.update(dict(building_area_draw=ahs_building_size))
                dist = DIST(floor_extent=False, **results)

                try:
                    fd.dist_model_score = dist.gibbs_sample()
                except ZeroDivisionError:
                    continue

                #print 'Updating {0} with the new DIST score: {1}.'.format(fd.name, fd.dist_model_score)

                if not options.get('dry_run'):
                    fd.save()

                dists.append((fd.id, fd.dist_model_score))

        print 'Updated dist scores: ', dists

