from django.contrib.gis.db import models


class PriorityDepartmentsManager(models.Manager):

    def get_queryset(self):
        return super(PriorityDepartmentsManager, self).get_queryset().filter(featured=True)