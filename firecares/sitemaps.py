from django.contrib import sitemaps
from firecares.firestation.models import FireDepartment
from django.db.models import Max
from django.core.urlresolvers import reverse


class BaseSitemap(sitemaps.Sitemap):

    def items(self):
        return ['media', 'models_performance_score', 'models_community_risk', 'safe_grades', 'login', 'contact_us',
                'firedepartment_list']

    def priority(self, item):
        return 1

    def location(self, item):
        return reverse(item)


class DepartmentsSitemap(sitemaps.Sitemap):
    max_population = 1

    def items(self):
        queryset = FireDepartment.objects.filter(archived=False)
        self.max_population = queryset.aggregate(Max('population'))['population__max']
        return queryset

    def location(self, item):
        return item.get_absolute_url()

    def priority(self, item):
        if item.featured is True:
            return 1
        if item.population is None:
            return 0
        # adding a bit to the total so featured items are always above others
        priority = item.population / float(self.max_population + 0.1)
        return priority

    def lastmod(self, item):
        return item.modified
