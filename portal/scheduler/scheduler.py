import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore

from portal.views import twitter_synchro, sbazar_synchro, bazos_synchro, elk_offers_synchro, elk_demands_synchro, \
    elk_words_synchro

logger = logging.getLogger(__name__)

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}


# functions to schedule
def twitter_job():
    # tw = twitter_synchro(count_per_word=100, include_word_context=True)
    twitter_synchro(count_per_word=100, include_word_context=True)


def sbazar_job():
    # sb = sbazar_synchro()
    sbazar_synchro()


def bazos_job():
    # baz = bazos_synchro()
    bazos_synchro()


def elk_offers_job():
    # elk_off = elk_offers_synchro()
    elk_offers_synchro()


def elk_demands_job():
    # elk_dem = elk_demands_synchro()
    elk_demands_synchro()


def elk_words_job():
    # elk_w = elk_words_synchro()
    elk_words_synchro()


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    # run this job every 24 hours
    # scheduler.add_job(deactivate_expired_accounts, 'interval', hours=24, name='clean_accounts', jobstore='default')

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
        trigger=CronTrigger(hour="1", minute="00"),
        id="sbazar_job",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job 'sbazar_job'.")

    scheduler.add_job(
        bazos_job,
        trigger=CronTrigger(hour="2", minute="00"),
        id="bazos_job",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job 'bazos_job'.")

    scheduler.add_job(
        elk_offers_job,
        trigger=CronTrigger(hour="3", minute="00"),
        id="elk_offers_job",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job 'elk_offers_job'.")

    scheduler.add_job(
        elk_demands_job,
        trigger=CronTrigger(hour="3", minute="30"),
        id="elk_demands_job",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job 'elk_demands_job'.")

    scheduler.add_job(
        elk_words_synchro,
        trigger=CronTrigger(hour="4", minute="00"),
        id="elk_words_synchro",  # The `id` assigned to each job MUST be unique
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job 'elk_words_synchro'.")

    # register_events(scheduler)
    scheduler.start()
    print("Scheduler started...")
