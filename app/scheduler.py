from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from flask import Flask

from . import jobs


def init_scheduler(app: Flask) -> BackgroundScheduler:
    """Initialize and start the APScheduler instance."""
    scheduler = BackgroundScheduler()

    def _job(func):
        def wrapper():
            with app.app_context():
                func()
        return wrapper

    scheduler.add_job(_job(jobs.nightly_sync_games), CronTrigger(hour=2))
    scheduler.add_job(
        _job(jobs.weekly_sync_player_stats),
        CronTrigger(day_of_week="sun", hour=3),
    )

    scheduler.start()
    return scheduler

