"""
import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from ...views import twitter_synchro, bazos_synchro, sbazar_synchro, elk_words_synchro, elk_demands_synchro, elk_offers_synchro

logger = logging.getLogger(__name__)

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}


def twitter_job():
    tw = twitter_synchro(count_per_word=100, include_word_context=True)

def sbazar_job():
    sb = sbazar_synchro()

def bazos_job():
    baz = bazos_synchro()

def elk_offers_job():
    elk_off = elk_offers_synchro()

def elk_demands_job():
    elk_dem = elk_demands_synchro()

def elk_words_job():
    elk_w = elk_words_synchro()


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way.
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
"""
# This job deletes APScheduler job execution entries older than `max_age` from the database.
# It helps to prevent the database from filling up with old historical records that are no
# longer useful.

# :param max_age: The maximum length of time to retain historical job execution records.
#                Defaults to 7 days.

"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            twitter_job,
            trigger=CronTrigger(hour="0", minute="30"),  # Every 10 seconds
            id="twitter_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'twitter_job'.")

        scheduler.add_job(
            sbazar_job,
            trigger=CronTrigger(hour="1", minute="30"),
            id="sbazar_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'sbazar_job'.")

        scheduler.add_job(
            bazos_job,
            trigger=CronTrigger(hour="2", minute="30"),
            id="bazos_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'bazos_job'.")

        scheduler.add_job(
            elk_offers_job,
            trigger=CronTrigger(hour="3", minute="30"),
            id="elk_offers_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'elk_offers_job'.")

        scheduler.add_job(
            elk_demands_job,
            trigger=CronTrigger(hour="4", minute="00"),
            id="elk_demands_job",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'elk_demands_job'.")

        scheduler.add_job(
            elk_words_synchro,
            trigger=CronTrigger(hour="4", minute="30"),
            id="elk_words_synchro",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'elk_words_synchro'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
"""
