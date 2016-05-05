from firecares.celery import app
from firecares.firestation.models import FireStation



@app.task(queue='qc')
def check_suggested_departments(station):
    """
    Checks a department's suggested departments.
    """

    return station, station.suggested_departments()

