import autocomplete_light.shortcuts as al
from .models import Address
from django.contrib.auth import get_user_model
from firecares.firestation.models import FireDepartment, FireStation

User = get_user_model()


al.register(Address,
            # Just like in ModelAdmin.search_fields
            search_fields=['address_line1', 'city', 'state_province', 'postal_code'],
            attrs={
                # This will set the input placeholder attribute:
                'placeholder': 'Address',
                # This will set the yourlabs.Autocomplete.minimumCharacters
                # options, the naming conversion is handled by jQuery
                'data-autocomplete-minimum-characters': 3,
            },
            # This will set the data-widget-maximum-values attribute on the
            # widget container element, and will be set to
            # yourlabs.Widget.maximumValues (jQuery handles the naming
            # conversion).
            widget_attrs={
                'data-widget-maximum-values': 100,
                # Enable modern-style widget !
                'class': 'modern-style',
            },)

al.register(FireDepartment,
            # Just like in ModelAdmin.search_fields
            search_fields=['name', 'fdid', 'id'],
            attrs={
                # This will set the input placeholder attribute:
                'placeholder': 'Fire Department',
                # This will set the yourlabs.Autocomplete.minimumCharacters
                # options, the naming conversion is handled by jQuery
                'data-autocomplete-minimum-characters': 1,
            },
            # This will set the data-widget-maximum-values attribute on the
            # widget container element, and will be set to
            # yourlabs.Widget.maximumValues (jQuery handles the naming
            # conversion).
            widget_attrs={
                'data-widget-maximum-values': 100,
                # Enable modern-style widget !
                'class': 'modern-style',
            },)


al.register(FireStation,
            # Just like in ModelAdmin.search_fields
            search_fields=['name'],
            attrs={
                # This will set the input placeholder attribute:
                'placeholder': 'Fire Station',
                # This will set the yourlabs.Autocomplete.minimumCharacters
                # options, the naming conversion is handled by jQuery
                'data-autocomplete-minimum-characters': 1,
            },
            # This will set the data-widget-maximum-values attribute on the
            # widget container element, and will be set to
            # yourlabs.Widget.maximumValues (jQuery handles the naming
            # conversion).
            widget_attrs={
                'data-widget-maximum-values': 100,
                # Enable modern-style widget !
                'class': 'modern-style',
            },)


# TODO: Check if this autocomplete is still needed
al.register(User,
            search_fields=['username'],
            attrs={
                'data-autocomplete-minimum-characters': 1,
            },
            choices=User.objects.filter(is_active=True)),


al.register(User,
            name='UserEmailAutocomplete',
            search_fields=['email'],
            attrs={
                'data-autocomplete-minimum-characters': 1,
            },
            choices=User.objects.filter(is_active=True).exclude(username='AnonymousUser'),
            choice_value=lambda self, choice: choice.email)
