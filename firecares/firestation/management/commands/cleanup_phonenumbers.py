from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from phonenumber_field.modelfields import PhoneNumber
import re

"""
This command is for cleaning up every phone and fax number in the
database. It removes all non-numeric characters, such as parenthesis,
hyphens, spaces, etc. It also removes prefixed 1s These numbers should
be made human-readable on the client side.
"""

def cleanNumber(no1):
    no2 = re.sub('[^0-9]','', no1)
    if no2.startswith("1"):
        no2 = no2[1:]
    return no2

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print("Don't worry, it always takes this long.")

        for fd in FireDepartment.objects.all():
            # If the FD has a phone number, clean it up
            if fd.headquarters_phone and not fd.headquarters_phone.raw_input == "Invalid Input":
                newPhone = cleanNumber(fd.headquarters_phone.raw_input)
                print(newPhone)
                fd.headquarters_phone = newPhone
            # If the FD has a fax number, clean it up
            if fd.headquarters_fax and not fd.headquarters_fax.raw_input == "Invalid Input":
                newFax = cleanNumber(fd.headquarters_fax.raw_input)
                print(newFax)
                fd.headquarters_fax = newFax
            # Save and continue to the next FD (if any)
            fd.save()

        print("Completed successfully!")
