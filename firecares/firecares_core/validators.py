from django.core.exceptions import ValidationError


def validate_choice(choices):
    def fn(value):
        choice_values = [x[0] for x in choices]
        if value not in choice_values:
            raise ValidationError('%s is not a valid choice in %s' % (value, choice_values))
    return fn
