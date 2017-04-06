import json
import elasticsearch
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from django.conf import settings

class Command(BaseCommand):
    help = 'Loads all departments in ElasticSearch.'

    def add_arguments(self, parser):
        parser.add_argument('--host', dest='host', default='localhost:9200')
        parser.add_argument('--region', dest='region', default='us-east-1')

    def handle(self, *args, **options):

        host = options.get('host')
        region = options.get('region')
        awsauth = AWS4Auth(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, region, 'es')

        es = Elasticsearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

        for fd in FireDepartment.objects.all():

            out = dict(id=fd.id,
                       fd_id=fd.fdid,
                       name=fd.name,
                       address_line1=fd.headquarters_address.address_line1,
                       address_line2=fd.headquarters_address.address_line2,
                       city=fd.headquarters_address.city,
                       state=fd.headquarters_address.state_province,
                       postal_code=fd.headquarters_address.postal_code,
                       country=fd.headquarters_address.country.iso_code,
                       modifed=fd.modified.isoformat())
            res = es.index(index='firecares', doc_type='department', id=fd.id, body=json.dumps(out))
            print res
            print 'Wrote {} to ES'.format(fd.name)
