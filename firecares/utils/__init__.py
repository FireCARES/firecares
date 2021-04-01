import inspect
import numbers
import re
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, fromstr
from enum import IntEnum
from functools import wraps


def dictfetchall(cursor):
    """
    Returns all rows from a cursor as a dict
    """
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def lenient_summation(*args, **kwargs):
    # Sums across all number-like items (True/False ARE considered numbers, 1/0 respectively),
    # if ALL items are not numbers, then return None
    mapping = kwargs.pop('mapping', None)
    if mapping:
        args = map(mapping, args)
    nums = filter(lambda x: isinstance(x, numbers.Number), args)
    if len(nums):
        return sum(nums)


def lenient_mean(*args, **kwargs):
    # Computes average across all number-like items (True/False ARE considered numbers, 1/0 respectively)
    # returns None if all items are None
    mapping = kwargs.pop('mapping', None)
    if mapping:
        args = map(mapping, args)
    items = filter(lambda x: isinstance(x, numbers.Number), args)
    if len(items):
        return sum(items) / float(max(len(items), 1))


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def get_email_domain(email):
    return re.match(r'(^[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$)', email).groups()[1].lower()


def get_property(obj, prop):
    dest_obj = prop.split('.')[:-1]
    src_prop = prop.split('.')[-1]

    for o in dest_obj:
        obj = getattr(obj, o)

    if obj:
        a = getattr(obj, src_prop)
        if callable(a):
            return a()
        else:
            return a

def to_multipolygon(geom):
    return GEOSGeometry(MultiPolygon(fromstr(geom.geojson),)) if geom.geom_type != 'MultiPolygon' else geom


class IntChoiceEnum(IntEnum):
    @classmethod
    def choices(cls):
        # get all members of the class
        members = inspect.getmembers(cls, lambda m: not(inspect.isroutine(m)))
        # filter down to just properties
        props = [m for m in members if not(m[0][:2] == '__')]
        # format into django choice tuple
        choices = tuple([(p[1].value, p[0]) for p in props])
        return choices


def when_not_testing(signal_handler):
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if settings.TESTING:
            return
        signal_handler(*args, **kwargs)
    return wrapper
