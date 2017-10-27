import os
from django import forms
from .models import Staffing, Document, FireDepartment, DataFeedback, FireStation

STATE_CHOICES = [{"name": "Any", "abbreviation": "AL"}, {"name": "Alabama", "abbreviation": "AL"}, {"name": "Alaska", "abbreviation": "AK"}, {"name": "American Samoa", "abbreviation": "AS"}, {"name": "Arizona", "abbreviation": "AZ"}, {"name": "Arkansas", "abbreviation": "AR"}, {"name": "California", "abbreviation": "CA"}, {"name": "Colorado", "abbreviation": "CO"}, {"name": "Connecticut", "abbreviation": "CT"}, {"name": "Delaware", "abbreviation": "DE"}, {"name": "District Of Columbia", "abbreviation": "DC"}, {"name": "Florida", "abbreviation": "FL"}, {"name": "Georgia", "abbreviation": "GA"}, {"name": "Guam", "abbreviation": "GU"}, {"name": "Hawaii", "abbreviation": "HI"}, {"name": "Idaho", "abbreviation": "ID"}, {"name": "Illinois", "abbreviation": "IL"}, {"name": "Indiana", "abbreviation": "IN"}, {"name": "Iowa", "abbreviation": "IA"}, {"name": "Kansas", "abbreviation": "KS"}, {"name": "Kentucky", "abbreviation": "KY"}, {"name": "Louisiana", "abbreviation": "LA"}, {"name": "Maine", "abbreviation": "ME"}, {"name": "Maryland", "abbreviation": "MD"}, {"name": "Massachusetts", "abbreviation": "MA"}, {"name": "Michigan", "abbreviation": "MI"}, {"name": "Minnesota", "abbreviation": "MN"}, {"name": "Mississippi", "abbreviation": "MS"}, {"name": "Missouri", "abbreviation": "MO"}, {"name": "Montana", "abbreviation": "MT"}, {"name": "Nebraska", "abbreviation": "NE"}, {"name": "Nevada", "abbreviation": "NV"}, {"name": "New Hampshire", "abbreviation": "NH"}, {"name": "New Jersey", "abbreviation": "NJ"}, {"name": "New Mexico", "abbreviation": "NM"}, {"name": "New York", "abbreviation": "NY"}, {"name": "North Carolina", "abbreviation": "NC"}, {"name": "North Dakota", "abbreviation": "ND"}, {"name": "Ohio", "abbreviation": "OH"}, {"name": "Oklahoma", "abbreviation": "OK"}, {"name": "Oregon", "abbreviation": "OR"}, {"name": "Pennsylvania", "abbreviation": "PA"}, {"name": "Puerto Rico", "abbreviation": "PR"}, {"name": "Rhode Island", "abbreviation": "RI"}, {"name": "South Carolina", "abbreviation": "SC"}, {"name": "South Dakota", "abbreviation": "SD"}, {"name": "Tennessee", "abbreviation": "TN"}, {"name": "Texas", "abbreviation": "TX"}, {"name": "Utah", "abbreviation": "UT"}, {"name": "Vermont", "abbreviation": "VT"}, {"name": "Virginia", "abbreviation": "VA"}, {"name": "Washington", "abbreviation": "WA"}, {"name": "West Virginia", "abbreviation": "WV"}, {"name": "Wisconsin", "abbreviation": "WI"}, {"name": "Wyoming", "abbreviation": "WY"}]


class StaffingForm(forms.ModelForm):

    class Meta:
        model = Staffing
        exclude = ['firestation']


class UploadFileForm(forms.Form):
    file = forms.FileField()


class DocumentUploadForm(forms.ModelForm):

    class Meta:
        model = Document
        exclude = ['department', 'filename']

    def __init__(self, *args, **kwargs):
        # Catch a passed in department pk that this document is associated with.
        self.department_pk = kwargs.pop('department_pk', None)
        super(DocumentUploadForm, self).__init__(*args, **kwargs)

    def clean_file(self):
        department = FireDepartment.objects.get(pk=self.department_pk)
        documents = Document.objects.filter(department=department)
        form_file = self.cleaned_data.get('file')

        # Prevent duplicate names.
        for document in documents:
            document_filename = os.path.basename(os.path.normpath(document.file.name))
            if document_filename == form_file.name:
                raise forms.ValidationError(
                    message="File with name '%(filename)s' already exists!",
                    code='file_already_exists',
                    params={'filename': form_file.name}
                )

        return form_file


class DepartmentUserApprovalForm(forms.Form):
    approved = forms.TypedChoiceField(coerce=lambda x: x == 'True', choices=((False, 'No'), (True, 'Yes')))
    email = forms.EmailField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=1024, required=False)

    def __init__(self, *args, **kwargs):
        super(DepartmentUserApprovalForm, self).__init__(*args, **kwargs)
        if self.data and not self.data.get('approved'):
            self.fields['message'].required = True


class DataFeedbackForm(forms.ModelForm):
    class Meta:
        model = DataFeedback
        fields = ('message', 'user', 'department', 'firestation')


class AddStationForm(forms.ModelForm):
    state = forms.ChoiceField(label=u'state', choices=STATE_CHOICES)

    class Meta:
        model = FireStation
        fields = ('name', 'station_number', 'station_address', 'address', 'state', 'city', 'zipcode', 'geom', 'department')
