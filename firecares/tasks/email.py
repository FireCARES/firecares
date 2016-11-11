from firecares.celery import app
from django.db import connection
from django.core.mail import mail_admins


@app.task(queue='email')
def send_mail(email):
    """
    Asynchronously sends an email.
    """
    return email.send()


@app.task(queue='email')
def ensure_valid_data():
    """
    Alert admins of bad data.
    """
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, st_area(geom) FROM firestation_firedepartment where st_area(geom)>6.99")
    messages = []

    for id, name, area in cursor.fetchall():
        messages.append('{0} ({1}) has an area of {2}.'.format(name, id, area))

    if messages:
        mail_admins('Invalid Geometries Detected', message='\n'.join(messages))

    cursor.execute("SELECT COUNT(*) FROM genericm2m_relatedobject;")
    generic_count = cursor.fetchone()

    if generic_count[0] < 2940:
        generic_count_message = "Related government units has dropped below 2,940."
        mail_admins('Low number of government units alert.', message=generic_count_message)
