import pandas as pd
from django.core.cache import cache
from django.db.models import IntegerField, Avg, Max, Min, Q
from django.utils.functional import cached_property
from firecares.utils import AttrDict
from firecares.firestation.managers import Ntile, Case, When


class FireDepartmentMetrics(object):
    def __init__(self, firedepartment, quartile_class, national_calculations):
        self.firedepartment = firedepartment
        self.quartile_class = quartile_class
        self.national_calculations = national_calculations
        self.peers = AttrDict()

    RISK_LEVELS = [(0, 'all'), (1, 'low'), (2, 'medium'), (4, 'high'), (5, 'unknown')]

    @cached_property
    def population_metrics_rows(self):
        """
        Returns the matching rows from the population metrics table.
        """
        return AttrDict({
            'low': self.quartile_class.objects.filter(id=self.firedepartment.id, level=1).first(),
            'medium': self.quartile_class.objects.filter(id=self.firedepartment.id, level=2).first(),
            'high': self.quartile_class.objects.filter(id=self.firedepartment.id, level=4).first(),
            'unknown': self.quartile_class.objects.filter(id=self.firedepartment.id, level=5).first(),
            'all': self.quartile_class.objects.filter(id=self.firedepartment.id, level=0).first()
        })

    @property
    def community_fire_risk(self):
        return AttrDict({
            'low': self.population_metrics_rows.low.risk_model_fires_quartile,
            'medium': self.population_metrics_rows.medium.risk_model_fires_quartile,
            'high': self.population_metrics_rows.high.risk_model_fires_quartile,
            'unknown': self.population_metrics_rows.unknown.risk_model_fires_quartile,
            'all': self.population_metrics_rows.all.risk_model_fires_quartile
        })

    @property
    def community_fire_spread_risk(self):
        return AttrDict({
            'low': self.population_metrics_rows.low.risk_model_size1_percent_size2_percent_sum_quartile,
            'medium': self.population_metrics_rows.medium.risk_model_size1_percent_size2_percent_sum_quartile,
            'high': self.population_metrics_rows.high.risk_model_size1_percent_size2_percent_sum_quartile,
            'unknown': self.population_metrics_rows.unknown.risk_model_size1_percent_size2_percent_sum_quartile,
            'all': self.population_metrics_rows.all.risk_model_size1_percent_size2_percent_sum_quartile
        })

    @property
    def community_death_and_injury_risk(self):
        return AttrDict({
            'low': self.population_metrics_rows.low.risk_model_deaths_injuries_sum_quartile,
            'medium': self.population_metrics_rows.medium.risk_model_deaths_injuries_sum_quartile,
            'high': self.population_metrics_rows.high.risk_model_deaths_injuries_sum_quartile,
            'unknown': self.population_metrics_rows.unknown.risk_model_deaths_injuries_sum_quartile,
            'all': self.population_metrics_rows.all.risk_model_deaths_injuries_sum_quartile
        })

    @cached_property
    def population_class_stats(self):
        """
        Returns summary statistics for calculation fields in the same population class.
        """

        if not self.firedepartment.population_class or self.firedepartment.archived:
            return []

        cache_key = 'population_class_{0}_stats'.format(self.firedepartment.population_class)
        cached = cache.get(cache_key)

        if cached:
            return cached

        fields = ['dist_model_score', 'risk_model_fires', 'risk_model_deaths_injuries_sum',
                  'risk_model_size1_percent_size2_percent_sum', 'residential_fires_avg_3_years']
        aggs = []

        for field in fields:
            aggs.append(Min(field))
            aggs.append(Max(field))
            aggs.append(Avg(field))

        low = self.quartile_class.objects.filter(population_class=self.firedepartment.population_class, level=1).aggregate(*aggs)
        med = self.quartile_class.objects.filter(population_class=self.firedepartment.population_class, level=2).aggregate(*aggs)
        high = self.quartile_class.objects.filter(population_class=self.firedepartment.population_class, level=4).aggregate(*aggs)
        unknown = self.quartile_class.objects.filter(population_class=self.firedepartment.population_class, level=5).aggregate(*aggs)
        all_levels = self.quartile_class.objects.filter(population_class=self.firedepartment.population_class, level=0).aggregate(*aggs)
        results = dict(low=low, medium=med, high=high, unknown=unknown, all=all_levels)
        cache.set(cache_key, results, timeout=60 * 60 * 24)
        return results

    @cached_property
    def residential_fires_3_year_avg(self):
        def get(level):
            return self.firedepartment.nfirsstatistic_set.filter(metric='residential_structure_fires',
                                                                 year__gte=2010,
                                                                 level=level).aggregate(Avg('count')).get('count__avg')
        low = get(1)
        medium = get(2)
        high = get(4)
        unknown = get(5)
        all_levels = get(0)

        return AttrDict({
            'low': low,
            'medium': medium,
            'high': high,
            'unknown': unknown,
            'all': all_levels
        })

    @cached_property
    def residential_fires_avg_3_years_breaks(self):
        """
        Risk model fire count breaks for the bullet chart
        """
        ret = AttrDict()
        for numlevel, level in self.RISK_LEVELS:
            vals = self.quartile_class.objects.get_field_stats('residential_fires_avg_3_years',
                                                               group_by='residential_fires_avg_3_years_quartile',
                                                               population_class=self.firedepartment.population_class,
                                                               level=numlevel)
            ret[level] = [n['max'] for n in vals]

        return ret

    @cached_property
    def risk_model_greater_than_size_2_breaks(self):
        """
        Size 2 or above fire breaks for the bullet chart
        """
        ret = AttrDict()
        for numlevel, level in self.RISK_LEVELS:
            vals = self.quartile_class.objects.get_field_stats('risk_model_size1_percent_size2_percent_sum',
                                                               group_by='risk_model_size1_percent_size2_percent_sum_quartile',
                                                               population_class=self.firedepartment.population_class,
                                                               level=numlevel)
            ret[level] = [n['max'] for n in vals]

        return ret

    @cached_property
    def risk_model_deaths_injuries_breaks(self):
        """
        Deaths and injuries for the bullet chart
        """
        ret = AttrDict()
        for numlevel, level in self.RISK_LEVELS:
            vals = self.quartile_class.objects.get_field_stats('risk_model_deaths_injuries_sum',
                                                               group_by='risk_model_deaths_injuries_sum_quartile',
                                                               population_class=self.firedepartment.population_class,
                                                               level=numlevel)
            ret[level] = [n['max'] for n in vals]

        return ret

    @cached_property
    def dist_model_risk_model_greater_than_size_2_quartile_avg(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.dist_model_risk_model_greater_than_size_2_quartile.mean()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_risk_model_deaths_injuries_quartile_avg(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.dist_model_risk_model_deaths_injuries_quartile_avg.mean()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_residential_fires_quartile_avg(self):
        """
        Used as the "Assessment of performance score based on the number of fires." Safe Grade
        """
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.dist_model_residential_fires_quartile_avg.mean()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_risk_model_greater_than_size_2_quartile_breaks(self):
        """
        Used as the "Assessment of performance score based on fire spread risk." Safe Grade
        """
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.groupby(['dist_model_risk_model_greater_than_size_2_quartile']).max()['dist_model_score'].tolist()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_risk_model_deaths_injuries_quartile_breaks(self):
        """
        Used as the "Assessment of performance score based on fire spread risk." Safe Grade
        """
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.groupby(['dist_model_risk_model_deaths_injuries_quartile']).max()['dist_model_score'].tolist()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_residential_fires_quartile_breaks(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.groupby(['dist_model_residential_fires_quartile']).max()['dist_model_score'].tolist()

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @property
    def assessment_of_performance_based_on_number_of_fires(self):
        return self.dist_model_residential_fires_quartile

    @property
    def assessment_of_performance_based_on_fire_spread(self):
        return self.dist_model_risk_model_greater_than_size_2_quartile

    @property
    def assessment_of_performance_based_on_death_and_injury_risk(self):
        return self.dist_model_risk_model_deaths_injuries_quartile

    @cached_property
    def dist_model_residential_fires_quartile(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.loc[df['id'] == self.firedepartment.id].dist_model_residential_fires_quartile.values[0]

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_risk_model_greater_than_size_2_quartile(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.loc[df['id'] == self.firedepartment.id].dist_model_risk_model_greater_than_size_2_quartile.values[0]

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def dist_model_risk_model_deaths_injuries_quartile(self):
        if not self.peers:
            self._get_peers()

        def get(df):
            if df is not None and not df.empty:
                return df.loc[df['id'] == self.firedepartment.id].dist_model_risk_model_deaths_injuries_quartile.values[0]

        return AttrDict({
            'low': get(self.peers.low),
            'medium': get(self.peers.medium),
            'high': get(self.peers.high),
            'unknown': get(self.peers.unknown),
            'all': get(self.peers.all)
        })

    @cached_property
    def national_risk_model_size1_percent_size2_percent_sum_quartile(self):
        # TODO: Need to optimize...
        ret = AttrDict()
        results = self.national_calculations.objects.filter(id=self.firedepartment.id)
        for numlevel, level in self.RISK_LEVELS:
            ret[level] = None
            for result in results:
                if result.level == numlevel:
                    ret[level] = result.risk_model_size1_percent_size2_percent_sum_quartile
        return ret

    @cached_property
    def national_risk_model_deaths_injuries_sum_quartile(self):
        # TODO: Need to optimize...
        ret = AttrDict()
        results = self.national_calculations.objects.filter(id=self.firedepartment.id)
        for numlevel, level in self.RISK_LEVELS:
            ret[level] = None
            for result in results:
                if result.level == numlevel:
                    ret[level] = result.risk_model_deaths_injuries_sum_quartile
        return ret

    @cached_property
    def nfirs_deaths_and_injuries_sum(self):
        def get(level):
            return self.firedepartment.nfirsstatistic_set.filter(Q(metric='civilian_casualties') | Q(metric='firefighter_casualties'),
                                                                 level=level,
                                                                 year__gte=2010).aggregate(Avg('count')).get('count__avg')

        low = get(1)
        medium = get(2)
        high = get(4)
        unknown = get(5)
        all_levels = get(0)

        return AttrDict({
            'low': low,
            'medium': medium,
            'high': high,
            'unknown': unknown,
            'all': all_levels
        })

    @cached_property
    def dist_model_score(self):
        return self._get_risk_model_field('dist_model_score')

    @cached_property
    def dist_model_score_fire_count(self):
        return self._get_risk_model_field('dist_model_score_fire_count')

    @cached_property
    def risk_model_deaths(self):
        return self._get_risk_model_field('risk_model_deaths')

    @cached_property
    def risk_model_injuries(self):
        return self._get_risk_model_field('risk_model_injuries')

    @cached_property
    def risk_model_fires(self):
        return self._get_risk_model_field('risk_model_fires')

    @cached_property
    def risk_model_fires_size0(self):
        return self._get_risk_model_field('risk_model_fires_size0')

    @cached_property
    def risk_model_fires_size0_percentage(self):
        return self._get_risk_model_field('risk_model_fires_size0_percentage')

    @cached_property
    def risk_model_fires_size1(self):
        return self._get_risk_model_field('risk_model_fires_size1')

    @cached_property
    def risk_model_fires_size1_percentage(self):
        return self._get_risk_model_field('risk_model_fires_size1_percentage')

    @cached_property
    def risk_model_fires_size2(self):
        return self._get_risk_model_field('risk_model_fires_size2')

    @cached_property
    def risk_model_fires_size2_percentage(self):
        return self._get_risk_model_field('risk_model_fires_size2_percentage')

    @cached_property
    def structure_counts_by_risk_category(self):
        return self._get_risk_model_field('structure_count')

    @cached_property
    def predicted_fires_sum(self):
        """
        Convenience method to sum
        """

        low, med, high, unknown, all_levels = self._get_risk_model_rows()

        def empty_fires(x):
            if x:
                return x.risk_model_fires_size0 is None and x.risk_model_fires_size1 is None \
                    and x.risk_model_fires_size2 is None

        def sum_fires(x):
            if x:
                return (x.risk_model_fires_size0 or 0) + (x.risk_model_fires_size1 or 0) + \
                    (x.risk_model_fires_size2 or 0)

        d = AttrDict({
            'low': None if empty_fires(low) else sum_fires(low),
            'medium': None if empty_fires(med) else sum_fires(med),
            'high': None if empty_fires(high) else sum_fires(high),
            'unknown': None if empty_fires(unknown) else sum_fires(unknown),
            'all': None if empty_fires(all_levels) else sum_fires(all_levels)
        })

        return d

    @cached_property
    def size2_and_greater_sum(self):
        """
        Convenience method to sum
        """

        low, med, high, unknown, all_levels = self._get_risk_model_rows()

        def empty_fires(x):
            if x:
                return x.risk_model_fires_size1 is None and x.risk_model_fires_size2 is None

        def sum_fires(x):
            if x:
                return (x.risk_model_fires_size1 or 0) + (x.risk_model_fires_size2 or 0)

        d = AttrDict({
            'low': None if empty_fires(low) else sum_fires(low),
            'medium': None if empty_fires(med) else sum_fires(med),
            'high': None if empty_fires(high) else sum_fires(high),
            'unknown': None if empty_fires(unknown) else sum_fires(unknown),
            'all': None if empty_fires(all_levels) else sum_fires(all_levels)
        })

        return d

    @cached_property
    def size2_and_greater_percentile_sum(self):
        """
        Convenience method to sum
        """

        low, med, high, unknown, all_levels = self._get_risk_model_rows()

        def empty_percentages(x):
            if x:
                return x.risk_model_fires_size1_percentage is None and x.risk_model_fires_size2_percentage is None

        def sum_fires(x):
            if x:
                return (x.risk_model_fires_size1_percentage or 0) + (x.risk_model_fires_size2_percentage or 0)

        d = AttrDict({
            'low': None if empty_percentages(low) else sum_fires(low),
            'medium': None if empty_percentages(med) else sum_fires(med),
            'high': None if empty_percentages(high) else sum_fires(high),
            'unknown': None if empty_percentages(unknown) else sum_fires(unknown),
            'all': None if empty_percentages(all_levels) else sum_fires(all_levels)
        })

        return d

    @cached_property
    def deaths_and_injuries_sum(self):

        low, med, high, unknown, all_levels = self._get_risk_model_rows()

        def empty_deaths(x):
            if x:
                return x.risk_model_deaths is None and x.risk_model_injuries is None

        def sum_deaths(x):
            if x:
                return (x.risk_model_deaths or 0) + (x.risk_model_injuries or 0)

        d = AttrDict({
            'low': None if empty_deaths(low) else sum_deaths(low),
            'medium': None if empty_deaths(med) else sum_deaths(med),
            'high': None if empty_deaths(high) else sum_deaths(high),
            'unknown': None if empty_deaths(unknown) else sum_deaths(unknown),
            'all': None if empty_deaths(all_levels) else sum_deaths(all_levels)
        })

        return d

    @cached_property
    def residential_structure_fire_counts(self):
        ret = AttrDict()
        for numlevel, level in self.RISK_LEVELS:
            v = self.firedepartment.nfirsstatistic_set.filter(metric='residential_structure_fires', level=numlevel)\
                .extra(select={
                       'year_max': 'SELECT MAX(COUNT) FROM firestation_nfirsstatistic b WHERE b.year = firestation_nfirsstatistic.year and b.metric=firestation_nfirsstatistic.metric and b.level = {level}'.format(level=numlevel)
                       })\
                .extra(select={
                       'year_min': 'SELECT MIN(COUNT) FROM firestation_nfirsstatistic b WHERE b.year = firestation_nfirsstatistic.year and b.metric=firestation_nfirsstatistic.metric and b.level = {level}'.format(level=numlevel)
                       })
            ret[level] = [dict(year=i.year, count=i.count, year_max=i.year_max, year_min=i.year_min) for i in v]

        return ret

    @cached_property
    def total_protected_structures(self):
        return self.firedepartment.firedepartmentriskmodels_set.get(level=0).structure_count

    def _get_risk_model_rows(self):
        return (self.firedepartment.firedepartmentriskmodels_set.filter(level=1).first(),
                self.firedepartment.firedepartmentriskmodels_set.filter(level=2).first(),
                self.firedepartment.firedepartmentriskmodels_set.filter(level=4).first(),
                self.firedepartment.firedepartmentriskmodels_set.filter(level=5).first(),
                self.firedepartment.firedepartmentriskmodels_set.filter(level=0).first())

    def _get_risk_model_field(self, field):
        """
        Return low/medium/high risk models
        """
        low, med, high, unknown, all_levels = self._get_risk_model_rows()

        return AttrDict({
            'low': getattr(low, field, None),
            'medium': getattr(med, field, None),
            'high': getattr(high, field, None),
            'unknown': getattr(unknown, field, None),
            'all': getattr(all_levels, field, None)
        })

    def _get_peers(self):
        object_values = self.population_metrics_rows
        for numlevel, level in self.RISK_LEVELS:
            if object_values[level]:
                similar_department_ids = self.firedepartment.similar_departments.values_list('id', flat=True)
                similar_and_self = list(similar_department_ids)
                similar_and_self.append(self.firedepartment.id)
                report_card_peers = self.quartile_class.objects.filter(id__in=similar_and_self, level=numlevel)
                report_card_peers = report_card_peers.annotate(dist_model_residential_fires_quartile=Case(When(
                    **{'dist_model_score__isnull': False,
                       'residential_fires_avg_3_years_quartile': object_values.get(level).residential_fires_avg_3_years_quartile,
                       'then': Ntile(4, output_field=IntegerField(),
                                     partition_by='dist_model_score is not null, residential_fires_avg_3_years_quartile, level',
                                     order_by='dist_model_score')}), output_field=IntegerField(), default=None))
                report_card_peers = report_card_peers.annotate(dist_model_risk_model_greater_than_size_2_quartile=Case(When(
                    **{'dist_model_score__isnull': False,
                       'risk_model_size1_percent_size2_percent_sum_quartile': object_values.get(level).risk_model_size1_percent_size2_percent_sum_quartile,
                       'then': Ntile(4, output_field=IntegerField(),
                                     partition_by='dist_model_score is not null, risk_model_size1_percent_size2_percent_sum_quartile, level',
                                     order_by='dist_model_score')}), output_field=IntegerField(), default=None))
                report_card_peers = report_card_peers.annotate(dist_model_risk_model_deaths_injuries_quartile=Case(When(
                    **{'dist_model_score__isnull': False,
                       'risk_model_deaths_injuries_sum_quartile': object_values.get(level).risk_model_deaths_injuries_sum_quartile,
                       'then': Ntile(4, output_field=IntegerField(),
                                     partition_by='dist_model_score is not null, risk_model_deaths_injuries_sum_quartile, level',
                                     order_by='dist_model_score')}), output_field=IntegerField(), default=None))

                self.peers[level] = pd.DataFrame(list(report_card_peers.values('id',
                                                                               'dist_model_score',
                                                                               'dist_model_residential_fires_quartile',
                                                                               'dist_model_risk_model_greater_than_size_2_quartile',
                                                                               'dist_model_risk_model_deaths_injuries_quartile')))
            else:
                self.peers[level] = None
