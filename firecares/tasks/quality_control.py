import requests
import csv
import tempfile

from celery import chord
from django.core import mail
from celery.exceptions import SoftTimeLimitExceeded
from firecares.celery import app
from firecares.firestation.models import FireDepartment
from django.conf import settings
from django.test import override_settings


@app.task(queue='quality-control', time_limit=120, soft=40)
def test_department_url(id):
    """
    Resolve a single departments url
    :param id: fire department id
    :return: error, fire_department_id
    """
    department = FireDepartment.objects.get(id=id)
    timeout = 30
    try:
        result = requests.head(department.website, timeout=timeout)

        # if the header request got redirected try a full get request
        if result.status_code != requests.codes.ok:
            result = requests.get(department.website, timeout=timeout)

        return result.status_code, id

    except requests.exceptions.RequestException as e:
        return e.message, id

    except SoftTimeLimitExceeded:
        return 'TimeLimitExceeded', id


@app.task(queue='quality-control')
@override_settings(ADMINS=(
    ('Mr. Ninja', 'my@email.com'),
))
def test_all_departments_urls_callback(results):
    """
    If fire department websites didn't resolve create an error report in CSV format,
    and email the admin with a link.
    :param results: chord results list in the form of error, fire_department_id
    """
    # Create the CSV file and add an error entry for every URL that didn't resolve with the department id
    send_report = False
    csv_file = tempfile.TemporaryFile()
    report_writer = csv.writer(csv_file)
    for result in results:
        if result[0] != requests.codes.ok:  # results items are in the form of error, fire_department_id
            report_writer.writerow(result)
            send_report = True

    if send_report:
        # TODO Save the CSV error report file on S3 and use a link in the email
        # Email admins with the error report attached
        email = mail.EmailMessage('Fire Department website link errors', 'See error report in the attached file',
                                  to=[admin[1] for admin in settings.ADMINS])
        csv_file.seek(0)
        email.attach("fd_website_error_report.csv", csv_file.read(), 'text/csv')
        email.send()

    csv_file.close()


@app.task(queue='quality-control')
def test_all_departments_urls():
    """
    Asynchronously resolve departments urls and record failures in a CSV file.
    """
    callback = test_all_departments_urls_callback.s()
    header = [test_department_url.si(fd.id) for fd in FireDepartment.objects.filter(archived=False, website__isnull=False)
              .exclude(website__exact='')]
    return chord(header)(callback)
