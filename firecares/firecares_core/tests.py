from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from .models import RecentlyUpdatedMixin


class CoreTests(TestCase):
    def test_recently_updated(self):
        """
        Tests the Recently Updated Mixin.
        """

        rum = RecentlyUpdatedMixin()
        rum.modified = timezone.now() - timedelta(days=11)
        self.assertFalse(rum.recently_updated)

        rum.modified = timezone.now() - timedelta(days=10)
        self.assertTrue(rum.recently_updated)
