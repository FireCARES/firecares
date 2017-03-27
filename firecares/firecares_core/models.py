from datetime import timedelta
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import timezone
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded
from jsonfield import JSONField
from time import sleep
from reversion import revisions as reversion
from django.conf import settings
from annoying.fields import AutoOneToOneField
from invitations.models import Invitation
from firecares.utils import get_email_domain
from guardian.shortcuts import assign_perm, remove_perm


class RecentlyUpdatedMixin(models.Model):
    """
    A mixin which adds a property that returns a boolean which represents if object was recently updated.
    """

    DAYS_CONSIDERED_RECENT = 10

    @property
    def recently_updated(self):
        try:
            diff = timezone.now() - self.modified
            return diff.days <= self.DAYS_CONSIDERED_RECENT
        except:
            return False

    class Meta:
        abstract = True


class Archivable(models.Model):
    """
    A mixin used to allow archiving objects.
    """

    archived = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Country(models.Model):
    """Model for countries"""
    iso_code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=45, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name", "iso_code"]


class Address(models.Model):
    """
    Model to store addresses
    """
    address_line1 = models.CharField("Address line 1", max_length=100)
    address_line2 = models.CharField("Address line 2", max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=False)
    state_province = models.CharField("State/Province", max_length=40, blank=True)
    postal_code = models.CharField("Postal Code", max_length=10)
    country = models.ForeignKey(Country, blank=False)
    geom = models.PointField(null=True, blank=True)
    objects = models.GeoManager()
    geocode_results = JSONField(null=True, blank=True)

    def get_row_display(self):
        return '{city}, {state_province}, {postal_code}' \
            .format(address_line1=self.address_line1, address_line2=self.address_line2, city=self.city,
                    state_province=self.state_province, postal_code=self.postal_code, country=self.country.iso_code)

    def get_full_display(self):
        return '{line1}{line2}, {city}, {state_province}, {postal_code}' \
            .format(line1=self.address_line1, line2=' ' + self.address_line2 if self.address_line2 else '', city=self.city,
                    state_province=self.state_province, postal_code=self.postal_code, country=self.country.iso_code)

    @classmethod
    def create_from_string(cls, query_string, dry_run=False):
        g = GoogleV3()
        try:
            results = g.geocode(query=query_string)
        except GeocoderQuotaExceeded:
            sleep(0.5)
            results = g.geocode(query=query_string)

        if results and results.latitude and results.longitude:
            params = dict(geom=Point(results.longitude, results.latitude))
            filter_components = lambda n: [c for c in results.raw['address_components'] if n in c['types']]  # noqa
            postal_codes = filter_components('postal_code')
            countries = filter_components('country')
            states = filter_components('administrative_area_level_1')
            cities = filter_components('locality')
            street_numbers = filter_components('street_number')
            street_names = filter_components('route')

            if postal_codes:
                params['postal_code'] = postal_codes[0]['short_name']

            if countries:
                params['country'], _ = Country.objects.get_or_create(iso_code=countries[0]['short_name'])

            if states:
                params['state_province'] = states[0]['short_name']

            if cities:
                params['city'] = cities[0]['long_name']

            if street_numbers and street_names:
                params['address_line1'] = '{0} {1}'.format(street_numbers[0]['short_name'], street_names[0]['short_name'])

            if not dry_run:
                try:
                    objs = cls.objects.get(**params)
                except cls.DoesNotExist:
                    objs = cls.objects.create(**params)
                return objs
            else:
                print 'Create new address with these parameters: {0}'.format(params)
                return cls(**params)

    def geocode(self):
        g = GoogleV3()
        query_string = self.get_row_display()
        try:
            results = g.geocode(query=query_string)
        except GeocoderQuotaExceeded:
            sleep(0.5)
            results = g.geocode(query=query_string)

        if results and results.latitude and results.longitude:
            self.geom = Point(results.longitude, results.latitude)
            self.geocode_results = results.raw
            self.save()

    @classmethod
    def batch_geocode(cls):
        for row in cls.objects.filter(geom__isnull=True, geocode_results__isnull=True):
            print row.get_row_display()
            row.geocode()

    def __unicode__(self):
        return "%s, %s %s" % (self.city, self.state_province,
                              str(self.country))

    class Meta:
        verbose_name_plural = "Addresses"
        unique_together = ("address_line1", "address_line2", "postal_code",
                           "city", "state_province", "country")


class ContactRequest(models.Model):
    """
    Model to store contact request information
    """
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.email)


# TODO: Extract "Approvable" abstract model for AccountRequst + DepartmentAssociationRequest
class AccountRequest(models.Model):
    """
    Model to store account requests.
    """
    STALE_DAYS = 5

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    department = models.ForeignKey('firestation.FireDepartment', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='approved_by_set')
    denied_at = models.DateTimeField(null=True, blank=True)
    denied_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='denied_by_set')

    @classmethod
    def stale_requests(cls):
        stale_end = timezone.now() - timedelta(days=cls.STALE_DAYS)
        return cls.objects.filter(approved_at__isnull=True, denied_at__isnull=True, created_at__lt=stale_end)

    @property
    def is_approved(self):
        return self.approved_by is not None

    @property
    def is_denied(self):
        return self.denied_by is not None

    def approve(self, approving_user):
        self.denied_by = None
        self.denied_at = None
        self.approved_by = approving_user
        self.approved_at = timezone.now()
        self.save()

    def deny(self, denying_user):
        self.approved_by = None
        self.approved_at = None
        self.denied_by = denying_user
        self.denied_at = timezone.now()
        self.save()

    def __unicode__(self):
        return "%s (%s)" % (self.email, self.created_at)


class UserProfile(models.Model):
    """
    Model to store additional user information.
    """
    user = AutoOneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    has_accepted_terms = models.BooleanField(default=False)
    functional_title = models.CharField(max_length=250, null=True, blank=True)
    department = models.ForeignKey('firestation.FireDepartment', null=True, blank=True)


class RegistrationWhitelist(models.Model):
    """
    Model to store a list of whitelisted domains/email addresses that can complete registration without intervention,
    may or may not have a department associated with them.  Having an assoicated department means this whitelisted row is specific
    to a particular department.
    """

    email_or_domain = models.CharField(max_length=200)
    # For department-specific whitelists, the "department", "created_by" and "created_at" fields will be populated,
    # department whitelists are different from global whitelists in that they the incoming user will be tied (in his/her UserProfile)
    # to the department after account activation and also assigned the permission if given on that specific department.
    department = models.ForeignKey('firestation.FireDepartment', null=True, blank=True)
    permission = models.CharField(max_length=255, null=True, blank=True)
    # For anonymous-user-submitted whitelist requests, they need to be vetted by a department admin
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('department', 'email_or_domain')

    def __unicode__(self):
        return unicode(self.email_or_domain)

    @property
    def is_domain_whitelist(self):
        return '@' not in self.email_or_domain

    @classmethod
    def _is_domain_only(cls, email):
        return '@' not in email

    @classmethod
    def get_for_email(cls, email):
        if cls.is_whitelisted(email):
            email_whitelists = cls.objects.filter(email_or_domain__contains='@')
            domain_whitelists = cls.objects.exclude(email_or_domain__contains='@')
            domain = get_email_domain(email)
            if email_whitelists.filter(email_or_domain=email).exists():
                return email_whitelists.filter(email_or_domain=email).first()
            else:
                return domain_whitelists.filter(email_or_domain=domain).first()

    def process_permission_assignment(self, user):
        if self.permission and self.department and user:
            for p in self.permission.split(','):
                if p:
                    assign_perm(p, user, self.department)

    @classmethod
    def is_whitelisted(cls, email):
        if not email:
            return False

        whitelists = cls.objects.values_list('email_or_domain', flat=True)
        email_whitelists = filter(lambda x: '@' in x, whitelists)
        domain_whitelists = set(whitelists) ^ set(email_whitelists)
        if cls._is_domain_only(email):
            return email in domain_whitelists

        domain = get_email_domain(email)
        pre_users = PredeterminedUser.objects.values_list('email', flat=True)
        if email in email_whitelists or domain in domain_whitelists or email in pre_users:
            return True
        else:
            return False

    @classmethod
    def is_department_whitelisted(cls, email):
        if not email:
            return False

        domain_whitelists = cls.objects.filter(department__isnull=False).exclude(email_or_domain__contains='@').values_list('email_or_domain', flat=True)
        if cls._is_domain_only(email):
            return email in domain_whitelists

        domain = get_email_domain(email)
        email_whitelists = cls.objects.filter(department__isnull=False, email_or_domain__contains='@').values_list('email_or_domain', flat=True)

        if email in email_whitelists or domain in domain_whitelists:
            return True
        else:
            return False

    @classmethod
    def for_department(cls, department):
        return cls.objects.filter(department=department)

    @classmethod
    def get_department_for_email(cls, email):
        if cls.is_department_whitelisted(email):
            if cls._is_domain_only(email):
                return cls.objects.filter(department__isnull=False, email_or_domain=email).first().department

            domain = get_email_domain(email)
            by_domain = cls.objects.filter(department__isnull=False, email_or_domain=domain).first()
            by_email = cls.objects.filter(department__isnull=False, email_or_domain=email).first()

            return by_email.department if by_email else by_domain.department


class DepartmentInvitation(models.Model):
    invitation = AutoOneToOneField(Invitation, on_delete=models.CASCADE)
    # If this foreign key doesn't allow for null, weird things can happen for AutoOneToOneFields
    department = models.ForeignKey('firestation.FireDepartment', on_delete=models.CASCADE, null=True)
    # Populated by the user account that accepts the invite AFTER the invite has been accepted AND user has registered
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

    def __unicode__(self):
        return u'{} - {}'.format(self.user.username, self.department.name)


class PredeterminedUser(models.Model):
    """
    PredeterminedUsers should be granted admin permissions on their associated department after their account has been created.
    """
    email = models.EmailField(unique=True)
    department = models.ForeignKey('firestation.FireDepartment')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    class Meta:
        unique_together = ('email', 'department')

    def __unicode__(self):
        return u'{} - {}'.format(self.email, self.department.name)


def default_requested_permission():
    return 1


class DepartmentAssociationRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    department = models.ForeignKey('firestation.FireDepartment')
    permission = models.CharField(max_length=100, default='admin_firedepartment')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='approved_association_requests_set')
    approved_at = models.DateTimeField(null=True, blank=True)
    denied_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='denied_assocation_requests_set')
    denied_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'{} - {}'.format(self.user.username, self.department.name)

    @property
    def is_approved(self):
        return self.approved_by is not None

    @property
    def is_denied(self):
        return self.denied_by is not None

    @classmethod
    def filter_by_email(cls, email):
        return cls.objects.filter(user__email=email)

    def approve(self, approving_user):
        self.denied_by = None
        self.denied_at = None
        self.approved_by = approving_user
        self.approved_at = timezone.now()
        self.save()
        return self._apply()

    def deny(self, denying_user):
        self.approved_by = None
        self.approved_at = None
        self.denied_by = denying_user
        self.denied_at = timezone.now()
        self.save()
        return self._apply()

    def _apply(self):
        if self.is_approved:
            assign_perm(self.permission, self.user, self.department)
            return True
        else:
            remove_perm(self.permission, self.user, self.department)
            return False

    @classmethod
    def user_has_association_request(cls, user):
        return cls.objects.filter(user=user).exists()


reversion.register(Address)
