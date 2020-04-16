from django import forms
from registration.forms import RegistrationFormUniqueEmail


class LimitedRegistrationForm(RegistrationFormUniqueEmail):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    def save(self, commit=True):
        user = super(LimitedRegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ChooseDepartmentForm(forms.Form):
    department = forms.IntegerField(required=True)
    state = forms.CharField(max_length=2, required=True)
