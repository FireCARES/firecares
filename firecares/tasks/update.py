from celery import task
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from firecares.firestation.models import FireDepartment
from fire_risk.models import DIST, NotEnoughRecords
from fire_risk.models.DIST.providers.ahs import ahs_building_areas
from fire_risk.models.DIST.providers.iaff import response_time_distributions
from fire_risk.backends.queries import RESIDENTIAL_FIRES_BY_FDID_STATE
from fire_risk.utils import LogNormalDraw
from firecares.utils import dictfetchall


def update_scores():
    for fd in FireDepartment.objects.all():
        update_performance_score.delay(fd.id)

@task(queue='update')
def update_performance_score(id, dry_run=False):
    """
    Updates department performance scores.
    """

    try:
        cursor = connections['nfirs'].cursor()
        fd = FireDepartment.objects.get(id=id)
    except (ConnectionDoesNotExist, FireDepartment.DoesNotExist):
        return

    cursor.execute(RESIDENTIAL_FIRES_BY_FDID_STATE, (fd.fdid, fd.state))
    results = dictfetchall(cursor)
    old_score = fd.dist_model_score
    counts = dict(object_of_origin=0, room_of_origin=0, floor_of_origin=0, building_of_origin=0, beyond=0)

    for result in results:
        if result['fire_sprd'] == '1':
            counts['object_of_origin'] += result['count']

        if result['fire_sprd'] == '2':
            counts['room_of_origin'] += result['count']

        if result['fire_sprd'] == '3':
            counts['floor_of_origin'] += result['count']

        if result['fire_sprd'] == '4':
            counts['building_of_origin'] += result['count']

        if result['fire_sprd'] == '5':
            counts['beyond'] += result['count']

    ahs_building_size = ahs_building_areas(fd.fdid, fd.state)

    if ahs_building_size is not None:
        counts['building_area_draw'] = ahs_building_size

    response_times = response_time_distributions.get('{0}-{1}'.format(fd.fdid, fd.state))

    if response_times:
        counts['arrival_time_draw'] = LogNormalDraw(*response_times, multiplier=60)

    try:
        dist = DIST(floor_extent=False, **counts)
        fd.dist_model_score = dist.gibbs_sample()

    except (NotEnoughRecords, ZeroDivisionError):
        fd.dist_model_score = None

    print 'updating fdid: {2} from: {0} to {1}.'.format(old_score, fd.dist_model_score, fd.id)

    if dry_run:
        return

    fd.save()


