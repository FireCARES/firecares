from django.contrib import sitemaps
from firecares.firestation.models import FireDepartment


class NavigationPages(object):
    featured = True  # priority 1
    modified = None
    url = None

    def __init__(self, url, modified=None):
        self.url = url
        self.modified = modified

    def get_absolute_url(self):
        return self.url


class BaseSitemap(sitemaps.Sitemap):

    max_population = 1

    def items(self):
        fds = FireDepartment.objects.all()
        # find the highest population value for the priority calculation
        for fd in fds:
            if fd.population > self.max_population:
                self.max_population = fd.population
        # make a list of all fire departments and add navigation pages
        items = []
        items.extend(fds)
        items.append(NavigationPages('/media'))
        items.append(NavigationPages('/performance-score'))
        items.append(NavigationPages('/community-risk'))
        items.append(NavigationPages('/'))
        items.append(NavigationPages('/login'))
        items.append(NavigationPages('/accounts/register'))
        items.append(NavigationPages('/#about'))
        items.append(NavigationPages('/#partners'))
        items.append(NavigationPages('/contact-us'))
        items.append(NavigationPages('/departments'))
        return items

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
