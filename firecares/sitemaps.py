from django.contrib import sitemaps
from firecares.firestation.models import FireDepartment


class BaseSitemap(sitemaps.Sitemap):

    max_population = 1

    def items(self):
        fds = FireDepartment.objects.all()
        # find the highest population value for the priority calculation
        for fd in fds:
            if fd.population > self.max_population:
                self.max_population = fd.population
        return fds

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
