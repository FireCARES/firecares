from django.contrib.auth import get_user_model
from django.test.client import Client
from django.core.urlresolvers import reverse
from favit.models import Favorite
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment, FireStation


User = get_user_model()


class TestFavorites(BaseFirecaresTestcase):
    def test_favorite_stations_list_view(self):
        """
        Tests the favorite stations list view.
        """
        fd = FireDepartment.objects.create(name='Fire Department 1')
        fs1 = FireStation.create_station(department=fd, address_string='1', name='Fire Station 1')
        fs2 = FireStation.create_station(department=fd, address_string='1', name='Fire Station 2')
        fs3 = FireStation.create_station(department=fd, address_string='1', name='Fire Station 3')
        # add these stations as favorites and remove the last one
        user = User.objects.get(username='admin')
        Favorite.objects.create(user, fs1)
        Favorite.objects.create(user, fs2)
        fav = Favorite.objects.create(user, fs3)
        fav.delete()

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.get(reverse('firestation_favorite_list'))
        self.assertTrue(fs1 in response.context['object_list'])
        self.assertTrue(fs2 in response.context['object_list'])
        self.assertTrue(fs3 not in response.context['object_list'])
        self.assertEqual(response.status_code, 200)

    def test_favorite_departments_list_view(self):
        """
        Tests the favorite departments list view.
        """
        fd1 = FireDepartment.objects.create(name='Fire Department 1')
        fd2 = FireDepartment.objects.create(name='Fire Department 2')
        fd3 = FireDepartment.objects.create(name='Fire Department 3')
        # add these departments as favorites and remove the last one
        user = User.objects.get(username='admin')
        Favorite.objects.create(user, fd1)
        Favorite.objects.create(user, fd2)
        fav = Favorite.objects.create(user, fd3)
        fav.delete()

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.get(reverse('firedepartment_list') + '?favorites=true')
        self.assertTrue(fd1 in response.context['object_list'])
        self.assertTrue(fd2 in response.context['object_list'])
        self.assertTrue(fd3 not in response.context['object_list'])
        self.assertEqual(response.status_code, 200)

        c.logout()

        try:
            response = c.get(reverse('firedepartment_list') + '?favorites=true')
        except:
            self.fail('Logged-out user triggering favorites search should not throw exception')
