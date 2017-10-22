from django.utils import timezone
from firecares.celery import app
from firecares.weather.models import WeatherWarnings, DepartmentWarnings


@app.task(queue='weather-task', rate_limit='15/m')
def collect_weather_noaa_warnings():
    """
    Adds data to the Weather warning table every 15 minutes because it tends to go down every once in a while
    This harvest can take up to 10 minutes to iterate through all warnings
    """
    WeatherWarnings.load_warning_data()


@app.task(queue='weather-task', rate_limit='24/h')
def cleanup_dept_weather_noaa_warnings():
    """
    Remove geometry from expired warnings in the department warning table
    """
    expired = timezone.now()
    print expired
    queryset = DepartmentWarnings.objects.filter(expiredate__lte=expired).exclude(warngeom=None)

    for departmentWarning in queryset:

        try:
            # set geomettry to a simple multipoloygon
            departmentWarning.warngeom = None
            departmentWarning.save()
            print "Department Warning cleaned for " + departmentWarning.departmentname + " expired " + str(departmentWarning.expiredate)

        except:
            print "Error removing Department Warning"
            return
