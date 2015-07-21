from django.forms import ModelForm, IntegerField
from .models import Staffing


class StaffingForm(ModelForm):

    class Meta:
        model = Staffing
        exclude = ['firestation']
