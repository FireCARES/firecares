from django import forms
from .models import Staffing


class StaffingForm(forms.ModelForm):

    class Meta:
        model = Staffing
        exclude = ['firestation']


class UploadFileForm(forms.Form):
    file = forms.FileField()