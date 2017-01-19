from .base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment


class ShimmedTests(BaseFirecaresTestcase):
    def test_open_close_transaction(self):
        """
        Test open/close transaction (by virtue of default Django test case)
        """

        FireDepartment.objects.all()
