from django.test import TestCase
from firecares.utils import lenient_summation, lenient_mean


class TestUtilityFunctions(TestCase):
    def test_permissive_functions(self):
        # Tests that the permissive functions perform correctly
        self.assertEqual(lenient_summation(1, 2, 3), 6)
        self.assertEqual(lenient_summation(1, None, 3), 4)
        self.assertEqual(lenient_summation(), None)
        self.assertEqual(lenient_summation(0), 0)
        # Make sure that mapping functions work correctly
        d = {'max': 1}
        d2 = {'max': 2}
        self.assertEqual(lenient_summation(None, d, d2, mapping=lambda x: x['max'] if x else None), 3)

        self.assertEqual(lenient_mean(1, 2, 3), 2)
        self.assertEqual(lenient_mean(1, None, 2), 1.5)
        self.assertEqual(lenient_mean(None, None, None), None)
        self.assertEqual(lenient_mean(0), 0)
        # Make sure that mapping functions work correctly
        d = {'avg': 1.5}
        d2 = {'avg': 2.5}
        self.assertEqual(lenient_mean(None, d, d2, mapping=lambda x: x['avg'] if x else None), 2)
