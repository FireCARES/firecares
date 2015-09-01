from firecares.celery import app

@app.task(queue='email')
def send_mail(email):
    """
    Asynchronously sends an email.
    """
    return email.send()
