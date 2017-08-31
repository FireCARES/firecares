from firecares.celery import app


@app.task(queue='singlenode')
def singlenodetask():
    print "HI"
