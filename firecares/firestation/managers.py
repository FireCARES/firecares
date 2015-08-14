from django.contrib.gis.db import models
from django.db.models import Func, Case, When


class PriorityDepartmentsManager(models.Manager):

    def get_queryset(self):
        return super(PriorityDepartmentsManager, self).get_queryset().filter(featured=True)


class Ntile(Func):
    function = 'ntile'
    template = '%(function)s(%(expressions)s) over (partition by %(order_by)s is not null order by %(order_by)s)'


class CalculationsQuerySet(models.QuerySet):
    def as_quartiles(self):
        qs = self

        for field in 'dist_model_score risk_model_deaths risk_model_injuries risk_model_fires_size0 \
                      risk_model_fires_size1 risk_model_fires_size2 risk_model_fires'.split():

            qs = qs.annotate(**{field+'_quartile': Case(When(**{field+'__isnull': False, 'then': Ntile(4, output_field=models.IntegerField(), order_by=field)}), output_field=models.IntegerField(), default=None)})

        return qs


class CalculationManager(models.GeoManager):
    """
    A geo-manager with FireCARES calculation methods.
    """
    def get_queryset(self):
        return CalculationsQuerySet(self.model, using=self._db)

    def metropolitan_departments(self):
        """
        Returns metropolitan departments.
        """
        return super(CalculationManager, self).get_queryset().filter(population__gte=1000000)
