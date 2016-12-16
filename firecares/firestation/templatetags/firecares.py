import json
from django import template
from django.conf import settings
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.template import defaultfilters
from django.template.defaulttags import URLNode, url
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext, ugettext as _, ungettext  # noqa
import phonenumbers

register = template.Library()

# A tuple of standard large number to their converters
intword_converters = (
    (3, lambda number: (
        ungettext('%(value).fk', '%(value).1fk', number),
        ungettext('%(value)sk', '%(value)sk', number),
    )),
    (6, lambda number: (
        ungettext('%(value).1fm', '%(value).1fm', number),
        ungettext('%(value)sm', '%(value)sm', number),
    )),
    (9, lambda number: (
        ungettext('%(value).1fb', '%(value).1fb', number),
        ungettext('%(value)sb', '%(value)sb', number),
    )),
    (12, lambda number: (
        ungettext('%(value).1ft', '%(value).1ft', number),
        ungettext('%(value)s trillion', '%(value)s trillion', number),
    )),
    (15, lambda number: (
        ungettext('%(value).1fq', '%(value).1fq', number),
        ungettext('%(value)s quadrillion', '%(value)s quadrillion', number),
    )),
)


@register.filter(is_safe=False)
def abbreviatedintword(value):
    """
    Converts a large integer to a friendly text representation. Works best
    for numbers over 1 million. For example, 1000000 becomes '1.0 million',
    1200000 becomes '1.2 million' and '1200000000' becomes '1.2 billion'.
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    def _check_for_i18n(value, float_formatted, string_formatted):
        """
        Use the i18n enabled defaultfilters.floatformat if possible
        """
        if settings.USE_L10N:
            value = defaultfilters.floatformat(value, 1)
            template = string_formatted
        else:
            template = float_formatted
        template = template % {'value': value}
        return template.replace('.0', '')

    for exponent, converters in intword_converters:
        large_number = 10 ** exponent
        if value < large_number * 1000:
            new_value = value / float(large_number)
            return _check_for_i18n(new_value, *converters(new_value))
    return value


@register.simple_tag
def url_replace(request, field, value):
    """
    Replaces or creates a GET parameter in a URL.
    """
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.filter(is_safe=False)
def risk_level(value):
    """
    Returns a string based risk level from a number.
    1: Low
    2: Medium
    3: Medium
    4: High
    """

    if value == 1:
        return 'low'

    if value == 2 or value == 3:
        return 'medium'

    if value == 4:
        return 'high'


@register.filter(is_safe=False)
def grade(value):
    """
    Returns a string based grade from a number.
    1: Good
    2: Fair
    3: Fair
    4: Poor
    """

    if value == 1:
        return 'good'

    if value == 2 or value == 3:
        return 'fair'

    if value == 4:
        return 'poor'


@register.filter(is_safe=False)
def quartile_text(value):
    """
    Replaces or creates a GET parameter in a URL.
    """

    return dict(zip(range(1, 5), ['lowest', 'second lowest', 'second highest', 'highest'])).get(value)


@register.filter(name='phonenumber')
def phonenumber(value, country='US', format=phonenumbers.PhoneNumberFormat.NATIONAL):
    """
    Converts raw phone numbers from the DB to national format.
    If the phone number does not exist do nothing.
    The template defaults to "Unknown" for nonexistent phone numbers.
    """
    if value:
        try:
            parsed = phonenumbers.parse(value.raw_input, country)
            return phonenumbers.format_number(parsed, format)
        except phonenumbers.NumberParseException:
            return value


@register.filter
def jsonify(obj):
    if isinstance(obj, QuerySet):
        return mark_safe(serialize('json', obj))
    return mark_safe(json.dumps(obj, cls=DjangoJSONEncoder, indent=4))


# Snagged from https://gist.github.com/kulturlupenguen/69aec1259131b5619fb7
class AbsoluteURL(str):
    pass


class AbsoluteURLNode(URLNode):
    def render(self, context):
        asvar, self.asvar = self.asvar, None
        path = super(AbsoluteURLNode, self).render(context)
        request_obj = context['request']
        abs_url = AbsoluteURL(request_obj.build_absolute_uri(path))

        if not asvar:
            return str(abs_url)
        else:
            if path == request_obj.path:
                abs_url.active = 'active'
            else:
                abs_url.active = ''
            context[asvar] = abs_url
            return ''


@register.tag
def absurl(parser, token):
    node = url(parser, token)
    return AbsoluteURLNode(
        view_name=node.view_name,
        args=node.args,
        kwargs=node.kwargs,
        asvar=node.asvar)
