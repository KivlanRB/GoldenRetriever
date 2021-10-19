from typing import DefaultDict
from pytz import utc
from time import sleep
from win10toast import ToastNotifier
from apscheduler.schedulers.qt import QtScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime

class Scheduler():

    __jobstore = {'default':SQLAlchemyJobStore("sqlite:///hector.sqlite")}
    __job_defaults = {'misfire_grace_time':None,'coalesce':True}
    apscheduler = QtScheduler(jobstores=__jobstore,job_defaults=__job_defaults)

    def __init__(self):
        self.notifier = ToastNotifier()
        self.jobs = self.apscheduler.get_jobs()
        self.apscheduler.start()
    
    def defaultFunc(self, title: str, msg: str):
        self.notifier.show_toast(title=title, msg=msg, duration=10, threaded=True)

    def add_date_job(self, date, title: str, msg: str, repeating: bool=False, weeks=None, days=None, hours=None, minutes=None, seconds=None):
        if(repeating == True): 
            self.apscheduler.add_job(self.defaultFunc, "trigger", [title, msg],start_date=date, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        self.apscheduler.add_job(self.defaultFunc, "date", [title, msg], run_date=date)