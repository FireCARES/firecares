import requests
from firecares.celery import app


@app.task(queue='slack')
def send_slack_message(_, url, message):
    """
    POSTs a message to slack.
    """
    return requests.post(url, json=message)
