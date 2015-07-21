from django.contrib.gis.db import models
from django.db.models import Q
import operator


class PriorityDepartmentsManager(models.Manager):

    DEPARTMENTS = {
        'Austin': {'state': 'TX', 'fdid': 'WP801'},
        'Arlington': {'state': 'VA', 'fdid': '01300'},
        'Chicago': {'state': 'IL', 'fdid': 'CS931'},
        'Phoenix': {'state': 'AZ', 'fdid': '08203'},
        'Mesa': {'state': 'AZ', 'fdid': '08183'},
        'Miami': {'state': 'FL', 'fdid': '01032'},
        'Memphis': {'state': 'TN', 'fdid': '79553'},
        'Seattle': {'state': 'WA', 'fdid': '17M15'},
        'Los Angeles': {'state': 'CA', 'fdid': '19105'},
        'Boston': {'state': 'MA', 'fdid': '25035'},
        'San Diego': {'state': 'CA', 'fdid': '37140'},
        'Detroit': {'state': 'MI', 'fdid': '08207'},
        'Atlanta': {'state': 'GA', 'fdid': '06001'},
        'Alexandria': {'state': 'VA', 'fdid': '51000'},
        'Worcester': {'state': 'MA', 'fdid': '27348'},
        'Nashville': {'state': 'TN', 'fdid': '19532'},
        'Charleston': {'state': 'SC', 'fdid': '10302'},
    }

    def get_priority_cities_filter(self):
        return reduce(operator.or_, [Q(**value) for key, value in self.DEPARTMENTS.items()])

    def get_query_set(self):
        return super(PriorityDepartmentsManager, self).get_query_set().filter(self.get_priority_cities_filter())
