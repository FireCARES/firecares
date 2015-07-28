from django.contrib.gis.db import models
from django.db.models import Q
import operator


class PriorityDepartmentsManager(models.Manager):

    def get_queryset(self):
        return super(PriorityDepartmentsManager, self).get_queryset().filter(featured=True)
