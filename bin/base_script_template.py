#!/usr/bin/env python


# Activate Virtualenv
import os
virtualenvs_root = os.environ.get('WORKON_HOME', '/usr/local/virtualenvs')
# MAKE SURE YOU CHANGE THE project_name IN THE FOLLOWING PATH SO THE FULL
# PATH TO activate_this.py IS CORRECT!
activate_this = '%s/project_name/bin/activate_this.py' % virtualenvs_root
execfile(activate_this, dict(__file__=activate_this))


# Setup the Django environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.core.management import setup_environ
from config import settings
setup_environ(settings)


# Import other needed modules for the script to run
from django.core.mail import mail_admins
from optparse import OptionParser
import sys, logging, time


def main():
    # ===========================================
    # = START THE MAIN BODY OF YOUR SCRIPT HERE =
    # ===========================================
    end = time.time()
    elapsed = end - start
    min = round(elapsed/60, 3)
    log.info("Script Finished\nIt took %s minutes to run the script." % min)


if __name__ == '__main__':

    # create logger
    # UPDATE THE FOLLOWING SO IT HAS THE CORRECT PYTHON PATH
    log = logging.getLogger("path.to.script")

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
        fh = logging.FileHandler(getattr(settings, 'LOG_DIR', '%s/logs/epaper_import.log' % settings.DJANGO_PROJECT_ROOT))
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        log.addHandler(fh)

    elif options.debug or options.verbose:

        # Setup logging to output to the console
        log.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    if len(args) == 1 and args[0] == 'help':
        parser.print_help()
    else:
        start = time.time()
        if settings.DEBUG:
            main()
        else:
            try:
                main()
            except:
                import traceback
                traceback_msg = '\n'.join(traceback.format_exception(*(sys.exc_info())))
                error_msg = "The script (%s) on SERVER HOST NAME created the following exception error:\n\n%s" % (os.path.abspath(__file__), traceback_msg)
                mail_admins('Log Test Error', error_msg)
