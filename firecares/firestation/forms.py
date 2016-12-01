import os
from django import forms
from .models import Staffing, Document, FireDepartment


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
