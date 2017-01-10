import requests
from StringIO import StringIO
from django.core.management import call_command
from django.db import connections
from django.test.client import Client
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment, FireDepartmentRiskModels, PopulationClassQuartile
from firecares.firestation.templatetags.firecares import quartile_text, risk_level


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
