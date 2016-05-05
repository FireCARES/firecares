import sys
import random
import datetime
import traceback
import time
import re
from django.db import InternalError
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireStation
from firecares.tasks.qc import check_suggested_departments

class Command(BaseCommand):
    help = 'Check if suggested departments match current ones.'

    def add_arguments(self, parser):
        parser.add_argument('--file',
                            '-f',
                            dest='file',
                            default=None,
                            help='File to read and append to.')

    def handle(self, *args, **options):

        def log(text, file):
            sys.stdout.write(text)
            sys.stdout.flush()
            file.write(text)

        mismatched_stations = []
        exception_stations = []
        last_id = 0
        is_finished = False
        regex_id = re.compile('(?<=id=)\\d+')

        # If a file was passed in, extract data from the log and start appending to it.
        if options['file']:
            logfile = open(options['file'], 'r')
            for line in logfile:
                if '~~~ FINISHED ~~~' in line:
                    is_finished = True
                    continue

                # Ignore extraneous info.
                if '~~~' in line:
                    continue

                if '... ' in line:
                    line_parts = line.split('... ')
                    if len(line_parts) < 2:
                        continue

                    left_part = line_parts[0]
                    right_part = line_parts[1]

                    if 'MISMATCH' in right_part:
                        mismatched_stations.append(left_part)
                    elif 'Traceback' in right_part:
                        exception_stations.append(left_part)

                    # Save off the last id so we can pick up where we left off.
                    if 'id' in left_part:
                        last_id = int(regex_id.search(left_part).group(0))

            logfile.close()
            logfile = open(options['file'], 'a')

            # Make sure we start on a new line.
            if not is_finished:
                log('\n', logfile)
        else:
            # Create a new log file and start writing to it.
            filename = 'check_suggested_departments (%s).log' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logfile = open(filename, 'w')
            log('~~~ CHECK SUGGESTED DEPARTMENTS ~~~\n\n', logfile)

        if not is_finished:
            stations_with_depts_to_check = FireStation.objects.filter(department__isnull=False, id__gt=last_id).extra(order_by=['id'])[:10]
            results = map(check_suggested_departments.delay, stations_with_depts_to_check)

            # loop through results and check if result.ready()
            # result.failed() will let you know if there was an exception
            # result.get() will get the output (suggested departments)

            completed = map(lambda task: task.ready(), results)
            while not all(completed):
                print '{0} out of {1} stations completed.  Waiting.'.format(len([n for n in completed if n]), stations_with_depts_to_check.count())
                time.sleep(10)
                completed = map(lambda task: task.ready(), results)

            for result in results:
                station, top_suggested_dept = result.get()
                name = '%s (id=%s)' % (station.name, station.id)
                log(name + '... ', logfile)

                if result.failed():
                    exception_stations.append(name)
                    #log(traceback.format_exc(), logfile)


                if station.department == top_suggested_dept:
                    log('OK\n', logfile)
                else:
                    mismatched_stations.append(name)
                    log('MISMATCH: (department = %s, top_suggested_dept = %s\n' % (station.department, top_suggested_dept), logfile)

            log('\n~~~ FINISHED ~~~\n', logfile)

        logfile.close()

        # Log analysis results in a different file to keep the main log clean.
        results_logfile = open(logfile.name.replace('.log', '.results.log'), 'w')
        stations_with_depts_count = FireStation.objects.filter(department__isnull=False).count()
        log('\nSTATIONS WITH DEPARTMENT: %s\n' % stations_with_depts_count, results_logfile)

        num_matched = stations_with_depts_count - len(mismatched_stations) - len(exception_stations)
        match_percentage = num_matched / float(stations_with_depts_count) * 100
        log('\nMATCH ACCURACY: %.2f%%\n' % match_percentage, results_logfile)

        # Match accuracy disregarding stations with exceptions.
        num_matched = stations_with_depts_count - len(mismatched_stations)
        match_percentage = num_matched / float(stations_with_depts_count) * 100
        log('\nMATCH ACCURACY (IGNORING EXCEPTIONS): %.2f%%\n' % match_percentage, results_logfile)

        if mismatched_stations:
            log('\n~~~~~~~~~~~~~~~~~~~~~~\n', results_logfile)
            log('  MISMATCHES (%s):' % len(mismatched_stations), results_logfile)
            log('\n~~~~~~~~~~~~~~~~~~~~~~\n', results_logfile)
            for name in mismatched_stations:
                log(name + '\n', results_logfile)

        if exception_stations:
            log('\n~~~~~~~~~~~~~~~~~~~~~~\n', results_logfile)
            log('  EXCEPTIONS (%s):' % len(exception_stations), results_logfile)
            log('\n~~~~~~~~~~~~~~~~~~~~~~\n', results_logfile)
            for name in exception_stations:
                log(name + '\n', results_logfile)

        results_logfile.close()
