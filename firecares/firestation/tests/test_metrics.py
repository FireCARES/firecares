import mock
import requests
from StringIO import StringIO
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.db import connections
from django.test.client import Client
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment, FireDepartmentRiskModels, PopulationClassQuartile
from firecares.firestation.templatetags.firecares_tags import quartile_text, risk_level
from firecares.tasks.update import update_performance_score, dist_model_for_hazard_level, update_nfirs_counts
from firecares.firecares_core.models import Address, Country
from fire_risk.models import DIST, DISTMediumHazard, DISTHighHazard


class FireDepartmentMetricsTests(BaseFirecaresTestcase):
    def test_convenience_methods(self):
        """
        Make sure the size2_and_greater_percentile_sum and deaths_and_injuries_sum methods do not throw errors.
        """
        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=1,
                                           department_type='test')

        FireDepartmentRiskModels.objects.create(department=fd)
        self.assertDictEqual(fd.metrics.size2_and_greater_percentile_sum, {'all': None, 'low': None, 'medium': None, 'high': None})
        self.assertDictEqual(fd.metrics.deaths_and_injuries_sum, {'all': None, 'low': None, 'medium': None, 'high': None})

        rm = fd.firedepartmentriskmodels_set.first()
        rm.risk_model_deaths = 1
        rm.save()
        fd.reload_metrics()
        self.assertEqual(fd.metrics.deaths_and_injuries_sum.low, 1)

        rm.risk_model_injuries = 1
        rm.save()
        fd.reload_metrics()
        self.assertEqual(fd.metrics.deaths_and_injuries_sum.low, 2)

        rm.risk_model_fires_size1_percentage = 1
        rm.save()
        fd.reload_metrics()
        self.assertEqual(fd.metrics.size2_and_greater_percentile_sum.low, 1)

        rm.risk_model_fires_size2_percentage = 1
        rm.save()
        fd.reload_metrics()
        self.assertEqual(fd.metrics.size2_and_greater_percentile_sum.low, 2)

    def test_population_metric_views(self):
        """
        Tests the population metric views.
        """
        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=9,
                                           department_type='test')

        fd_archived = FireDepartment.objects.create(name='Test db',
                                                    population=0,
                                                    population_class=9,
                                                    department_type='test',
                                                    archived=True)

        FireDepartmentRiskModels.objects.create(department=fd)
        FireDepartmentRiskModels.objects.create(department=fd_archived)

        # update materialized view manually after adding new record
        cursor = connections['default'].cursor()
        cursor.execute("REFRESH MATERIALIZED VIEW population_quartiles;")

        self.assertTrue(PopulationClassQuartile.objects.filter(id=fd.id).first())

        # Ensure archived departments are not included in quartile results.
        self.assertNotIn(fd_archived.id, PopulationClassQuartile.objects.all().values_list('id', flat=True))

        # make sure the population class logic works
        self.assertTrue(fd.metrics.population_class_stats)

        # make sure the department page does not return an error
        c = Client()
        c.login(**self.admin_creds)
        response = c.get(fd.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        # make sure the department page does not return an error for archived departments
        response = c.get(fd_archived.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_quartile_text(self):
        """
        Tests the quartile text template tag.
        """
        self.assertEqual('lowest', quartile_text(1))
        self.assertEqual('second lowest', quartile_text(2))
        self.assertEqual('second highest', quartile_text(3))
        self.assertEqual('highest', quartile_text(4))
        self.assertIsNone(quartile_text(5))

    def test_risk_level(self):
        """
        Tests the quartile text template tag.
        """
        self.assertEqual('low', risk_level(1))
        self.assertEqual('medium', risk_level(2))
        self.assertEqual('medium', risk_level(3))
        self.assertEqual('high', risk_level(4))
        self.assertIsNone(risk_level(5))

    def test_performance_model_urls(self):
        """
        Make HEAD requests to ensure external sites work.
        """

        urls = [
            'http://www.nist.gov/el/fire_research/upload/Report-on-Residential-Fireground-Field-Experiments.pdf',  # NIST TN 1661
            'http://www.nfpa.org/codes-and-standards/document-information-pages?mode=code&code=1710'  # NFPA 1710
        ]

        for url in urls:
            response = requests.head(url, allow_redirects=True)
            self.assertEqual(response.status_code, 200, 'Url: {0} did not return a 200.'.format(url))

        get_urls = [
            'http://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1797.pdf',  # NIST TN 1797
        ]

        # Hack to get around fact that nist.gov returns a 404 for HEAD requests to the NIST.TN.1797.pdf, but a 200 for GETs :/
        for url in get_urls:
            response = requests.get(url, headers={'Range': 'bytes=0-0'})
            self.assertEqual(response.status_code, 206, 'Url: {0} did not return a 206.'.format(url))

    def test_prediction_import(self):
        fd = FireDepartment.objects.create(id=92679,
                                           name='Test import',
                                           population=0,
                                           population_class=1,
                                           department_type='test')

        fd2 = FireDepartment.objects.create(id=79344,
                                            name='Test import 2',
                                            population=0,
                                            population_class=1,
                                            department_type='test')
        # Create existing low risk model
        FireDepartmentRiskModels.objects.create(department=fd, level=1,
                                                risk_model_deaths=2, risk_model_injuries=3,
                                                risk_model_fires_size0=5, risk_model_fires_size1=7,
                                                risk_model_fires_size2=1)

        FireDepartmentRiskModels.objects.create(department=fd2, level=1,
                                                risk_model_deaths=2)

        call_command('import-predictions', 'firecares/firestation/tests/mock/predictions.csv', stdout=StringIO())

        # Shoud have a total of 31 fires across size0, size1 and size2
        self.assertEqual(fd.metrics.risk_model_fires.low, 31)
        self.assertEqual(fd.metrics.risk_model_fires_size0.low, 28)

        # Having an NA value that should be considered 0 in the summation
        self.assertEqual(fd.metrics.risk_model_fires_size0.medium, 18)
        self.assertEqual(fd.metrics.risk_model_fires_size2.high, 5)

        # Test to make sure that existing data isn't overwritten in the case of incoming NA values
        self.assertEqual(fd2.metrics.risk_model_deaths.low, 2)

        # Percentages should add up to 1
        lr_fire_percent = (fd.metrics.risk_model_fires_size0_percentage.low +
                           fd.metrics.risk_model_fires_size1_percentage.low +
                           fd.metrics.risk_model_fires_size2_percentage.low)
        self.assertAlmostEqual(1, lr_fire_percent)

        # Ensure that aggregated "ALL" risk level rows are created
        self.assertEqual(len(fd.firedepartmentriskmodels_set.all()), 4)
        self.assertEqual(len(fd2.firedepartmentriskmodels_set.all()), 4)

    @mock.patch("psycopg2.connect")
    def test_update_nfirs(self, mock_connect):

        us = Country.objects.create(iso_code='US', name='United States')

        address = Address.objects.create(address_line1='Test', country=us,
                                         geom=Point(-118.42170426600454, 34.09700463377199))
        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA',
                                             headquarters_address=address, featured=0, archived=0)

        # ensure no risk model data before run
        self.assertFalse(lafd.firedepartmentriskmodels_set.all())

        query_result = [
            (u'High', 30L, 44L, 16L, 13L, 9L),
            (u'Low', 179L, 376L, 21L, 139L, 34L),
            (u'Medium', 51L, 147L, 12L, 41L, 7L),
            (u'N/A', 1L, 52L, 192L, 18L, 66L)
        ]
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        mock_cur.description = [('risk_category',), ('1',), ('2',), ('3',), ('4',), ('5',)]
        mock_cur.fetchall.return_value = query_result
        update_performance_score(lafd.id)

        self.assertEqual(lafd.firedepartmentriskmodels_set.all().count(), 4)

        # ensure risk model data was created and the dist_model_score was populated correctly
        for i in ['0', '1', '2', '4']:
            queryset = lafd.firedepartmentriskmodels_set.filter(level=i)
            self.assertEqual(queryset.count(), 1)
            self.assertTrue(queryset.filter(dist_model_score__isnull=False))

    def test_dist_model_hazard_level(self):

        self.assertEqual(dist_model_for_hazard_level('High'), DISTHighHazard)
        self.assertEqual(dist_model_for_hazard_level('Medium'), DISTMediumHazard)
        self.assertEqual(dist_model_for_hazard_level('All'), DIST)
        self.assertEqual(dist_model_for_hazard_level('Low'), DIST)

    @mock.patch("psycopg2.connect")
    def test_pull_nfirs_statistics(self, mock_connect):

        us = Country.objects.create(iso_code='US', name='United States')

        address = Address.objects.create(address_line1='Test', country=us,
                                         geom=Point(-118.42170426600454, 34.09700463377199))
        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA',
                                             headquarters_address=address, featured=0, archived=0)

        class MockNFIRSCursor(object):
            def __init__(self):
                self.responses = [
                    ((2L, 2014.0, u'N/A'),
                     (2L, 2012.0, u'Low'),
                     (4L, 2012.0, u'N/A'),
                     (11L, 2011.0, u'Low'),
                     (43L, 2011.0, u'Medium'),
                     (2L, 2011.0, u'N/A'),
                     (2L, 2010.0, u'Low'),
                     (1L, 2010.0, u'Medium'),
                     (2L, 2010.0, u'N/A')),

                    ((1L, 2014.0, u'High'),
                     (8L, 2014.0, u'Low'),
                     (4L, 2014.0, u'Medium'),
                     (9L, 2014.0, u'N/A'),
                     (1L, 2013.0, u'High'),
                     (9L, 2013.0, u'Low'),
                     (8L, 2013.0, u'Medium'),
                     (5L, 2013.0, u'N/A'),
                     (12L, 2012.0, u'Low'),
                     (7L, 2012.0, u'Medium'),
                     (11L, 2012.0, u'N/A'),
                     (1L, 2011.0, u'High'),
                     (24L, 2011.0, u'Low'),
                     (6L, 2011.0, u'Medium'),
                     (6L, 2011.0, u'N/A'),
                     (17L, 2010.0, u'Low'),
                     (7L, 2010.0, u'Medium'),
                     (21L, 2010.0, u'N/A')),

                    ((2L, 2014.0, u'Low'),
                     (1L, 2014.0, u'Medium'),
                     (2L, 2014.0, u'N/A'),
                     (1L, 2013.0, u'Medium'),
                     (2L, 2012.0, u'Low'),
                     (4L, 2012.0, u'Medium'),
                     (4L, 2012.0, u'N/A'),
                     (7L, 2011.0, u'Low'),
                     (1L, 2011.0, u'Medium'),
                     (1L, 2011.0, u'N/A'),
                     (6L, 2010.0, u'Low'),
                     (2L, 2010.0, u'Medium'),
                     (2L, 2010.0, u'N/A')),

                    ((2014L,),
                     (2013L,),
                     (2012L,),
                     (2011L,),
                     (2010L,))
                ]

            def execute(self, query, params=None):
                if 'FROM ffcasualty a' in query:
                    self.response = self.responses[0]
                elif 'FROM buildingfires a' in query:
                    self.response = self.responses[1]
                elif 'FROM civiliancasualty a' in query:
                    self.response = self.responses[2]
                else:
                    self.response = self.responses[3]

            def fetchall(self):
                return self.response

            def close(self):
                pass

        self.assertEqual(lafd.nfirsstatistic_set.count(), 0)

        mock_con = mock_connect.return_value
        mock_con.cursor.return_value = MockNFIRSCursor()

        update_nfirs_counts(lafd.id)

        # Should have 1 for each of the 5 level buckets (including the N/As) per year (5) per statistic (3)
        self.assertEqual(lafd.nfirsstatistic_set.count(), 3 * 5 * 5)
        self.assertEqual(lafd.nfirsstatistic_set.get(year=2014, level=0, metric='residential_structure_fires').count, 22L)

        # Ensure that even for years with no counts, a statistic row is in place
        self.assertEqual(lafd.nfirsstatistic_set.filter(year=2013, metric='firefighter_casualties').count(), 5)

        # Years w/ no counts should be None, not 0
        self.assertIsNone(lafd.nfirsstatistic_set.get(year=2013, level=0, metric='firefighter_casualties').count)

        self.assertEqual(lafd.nfirsstatistic_set.get(year=2010, level=1, metric='civilian_casualties').count, 6L)
