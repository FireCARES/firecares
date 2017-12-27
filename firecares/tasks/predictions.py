from firecares.celery import app


@app.task(queue='singlenode')
def import_predictions():
    pass
