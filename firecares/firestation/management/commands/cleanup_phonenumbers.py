from __future__ import division
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import NumberParseException
import re

valid = []
invalid = []

class Command(BaseCommand):
    """
    This command is for cleaning up every phone and fax number in the
    database. It removes all non-numeric characters, such as parenthesis,
    hyphens, spaces, etc. It also removes prefixed 1s These numbers should
    be made human-readable on the client side.
    """

    def handle(self, *args, **kwargs):
        print("Don't worry, it always takes this long.")

        for fd in FireDepartment.objects.all():
            # If the FD has a phone number, clean it up
            if fd.headquarters_phone and not fd.headquarters_phone.raw_input == "Invalid Input":
                try:
                    new_phone = PhoneNumber.from_string(fd.headquarters_phone.raw_input)

                    if new_phone.is_valid():
                        fd.headquarters_phone = new_phone
                        valid.append(new_phone)
                    else:
                        invalid.append(new_phone)
                        fd.headquarters_phone = None

                except NumberParseException:
                    invalid.append(new_phone)
                    fd.headquarters_phone = None

            # If the FD has a fax number, clean it up
            if fd.headquarters_fax and not fd.headquarters_fax.raw_input == "Invalid Input":
                try:
                    new_fax = PhoneNumber.from_string(fd.headquarters_fax.raw_input)

                    if new_fax.is_valid():
                        fd.headquarters_fax = new_fax
                        valid.append(new_fax)
                    else:
                        invalid.append(new_fax)
                        fd.headquarters_fax = None

                except NumberParseException:
                    invalid.append(new_fax)
                    fd.headquarters_fax = None

            # Save and continue to the next FD (if any)
            fd.save()

        print 'Valid Numbers: {}'.format(len(valid))
        print 'Invalid numbers: {}'.format(len(invalid))
        print 'Invald percent: {}'.format(len(invalid) / (len(valid) + len(invalid)))
        print 'Invalid numbers: ', map(str, invalid)

        print("Completed successfully!")
