from firecares.celery import app
from django.contrib.auth.models import User

@app.task(queue='email')
def send_mail(email):
    email.send()
