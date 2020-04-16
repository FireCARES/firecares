import phonenumbers
from django.core.serializers.json import DjangoJSONEncoder
from firecares.firestation.models import PopulationClassQuartile


class FireCARESJSONSerializer(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, PopulationClassQuartile):
            o = o.__dict__
            del o['_state']
            del o['geom']
            return o
        elif isinstance(o, phonenumbers.PhoneNumber):
            return o.as_national
        else:
            return super(FireCARESJSONSerializer, self).default(o)
