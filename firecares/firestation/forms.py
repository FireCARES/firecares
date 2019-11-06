import os
from django import forms
from .models import Staffing, Document, FireDepartment, DataFeedback, FireStation
from mapwidgets.widgets import GooglePointFieldWidget


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

    class Meta:
        model = FireStation
        fields = ('name', 'station_number', 'address')
        widgets = {
            'address': GooglePointFieldWidget,
        }

    def __init__(self, *args, **kwargs):
        # Catch a passed in department pk that this document is associated with.
        self.department_pk = kwargs.pop('department_pk', None)
        super(AddStationForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        des = self.cleaned_data['name']
        if not des:
            raise forms.ValidationError("name cannot be empty")
        return des
