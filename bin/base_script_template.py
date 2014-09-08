#!/usr/bin/env python


# Activate Virtualenv
import os
virtualenvs_root = os.environ.get('WORKON_HOME', '/usr/local/virtualenvs')
# MAKE SURE YOU CHANGE THE django_base_site IN THE FOLLOWING PATH SO THE FULL
# PATH TO activate_this.py IS CORRECT!
activate_this = '%s/django_base_site/bin/activate_this.py' % virtualenvs_root
execfile(activate_this, dict(__file__=activate_this))


# Setup the Django environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.management import setup_environ
from config import settings
setup_environ(settings)


# Import other needed modules for the script to run
from django.core.mail import mail_admins
from optparse import OptionParser
import sys
import logging
import time


def end_timer():
    end_time = time.time()
    elapsed = end_time - start_time
    min = round(elapsed / 60, 3)
    log.info("Script Finished\nIt took %s minutes to run the script." % min)


def main():
    # ===========================================
    # = START THE MAIN BODY OF YOUR SCRIPT HERE =
    # ===========================================
    pass


if __name__ == '__main__':

    error_email_subject = 'SCRIPT ERROR SUBJECT'
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # create logger
    log = logging.getLogger(script_name)

    # Set script options
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Be verbose.")
    parser.add_option("-n", "--dry-run",
                      action="store_true", dest="dry_run", default=False,
                      help="don't copy any files or write anything to the database")
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Print debug messages")
    parser.add_option("-F", "--log-to-file",
                      action="store_true", dest="log_to_file", default=False,
                      help="Log messages to a log file.")
    (options, args) = parser.parse_args()

    if options.log_to_file:

        log.setLevel(logging.INFO)
        fh = logging.FileHandler(getattr(settings, 'LOG_DIR', '%s/logs/%s.log' % (settings.DJANGO_PROJECT_ROOT, script_name)))
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        log.addHandler(fh)

    elif options.debug or options.verbose:

        # Setup logging to output to the console
        log.setLevel(logging.INFO)
        if options.debug:
            log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    if len(args) == 1 and args[0] == 'help':
        parser.print_help()
    else:
        start_time = time.time()
        if settings.DEBUG:
            main()
            end_timer()
        else:
            try:
                main()
                end_timer()
            except:
                import traceback
                traceback_msg = '\n'.join(traceback.format_exception(*(sys.exc_info())))
                error_msg = "The script (%s) on %s created the following exception error:\n\n%s" % (script_name, os.uname()[1], traceback_msg)
                mail_admins(error_email_subject, error_msg)
