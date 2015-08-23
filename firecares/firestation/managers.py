from django.contrib.gis.db import models
from django.db.models import Func, Case, When, Q, Min, Max, Avg
from django.db.models.expressions import RawSQL
from django.db.models import Aggregate
from django.db.models import FloatField

class PriorityDepartmentsManager(models.Manager):

    def get_queryset(self):
        return super(PriorityDepartmentsManager, self).get_queryset().filter(featured=True)


class Ntile(Func):
    function = 'ntile'
    template = '%(function)s(%(expressions)s) over (partition by %(partition_by)s is not null order by %(order_by)s)'


class SumNtile(Func):
    """
    NTile over two fields
    """
    function = 'ntile'
    template = '%(function)s(%(expressions)s) over (partition by COALESCE(%(field_1)s,0)+COALESCE(%(field_2)s,0) != 0 order by COALESCE(%(field_1)s,0)+COALESCE(%(field_2)s,0))'


class FilteredAvg(Aggregate):
    function = 'AVG'
    name = 'Avg'
    template = '%(function)s(%(expressions)s) %(where)s'

    def __init__(self, expression, **extra):
        super(FilteredAvg, self).__init__(expression, output_field=FloatField(), **extra)

    def convert_value(self, value, expression, connection, context):
        if value is None:
            return value
        return float(value)

class CalculationsQuerySet(models.QuerySet):

    def as_quartiles(self):
        qs = self


        fields = 'dist_model_score risk_model_deaths risk_model_injuries risk_model_fires_size0 \
                      risk_model_fires_size1 risk_model_fires_size2 risk_model_fires'.split()

        # dynamically add sum fields
        for field1, field2, fieldname in [('risk_model_fires_size1_percentage', 'risk_model_fires_size2_percentage', 'risk_model_size1_percent_size2_percent_sum'),
                               ('risk_model_deaths', 'risk_model_injuries', 'risk_model_deaths_injuries_sum')]:

            qs = qs.extra(select={fieldname: 'SELECT COALESCE({0},0)+COALESCE({1},0)'.format(field1, field2)})
            qs = qs.annotate(**{'{0}_quartile'.format(fieldname): Case(When(Q(**{field1+'__isnull': False}) | Q(**{field2+'__isnull': False}), then=SumNtile(4, output_field=models.IntegerField(), field_1=field1, field_2=field2)), output_field=models.IntegerField(), default=None)})


        for field in fields:
            qs = qs.annotate(**{field+'_quartile': Case(When(**{field+'__isnull': False, 'then': Ntile(4, output_field=models.IntegerField(), partition_by=field, order_by=field)}), output_field=models.IntegerField(), default=None)})

        qs = qs.annotate(val=RawSQL("SELECT AVG(count) FROM firestation_nfirsstatistic WHERE fire_department_id=firestation_firedepartment.id and year >= extract(year FROM CURRENT_DATE) - 3", ()))

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

    def get_field_stats(self, field, group_by=None, qs=None):
        """
        Provides summary statistics for a field, with an optional group by value.
        """

        if not qs:
            qs = super(CalculationManager, self).get_queryset().filter(**{field + '__isnull': False})

        if group_by:
            qs = qs.values(group_by)

        return qs.annotate(min=Min(field), max=Max(field), avg=Avg(field))


#SELECT
#CASE WHEN "population_class_5_quartiles"."dist_model_score" IS NOT NULL
#    THEN ntile(4) over (partition by dist_model_score is not null, residential_fires_avg_3_years_quartile  order by residential_fires_avg_3_years_quartile) ELSE NULL END AS "risk_model_fires_size0_quartile" from population_class_5_quartiles