from typing import DefaultDict
from pytz import utc
from time import sleep
from win10toast import ToastNotifier
from apscheduler.schedulers.qt import QtScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

class Scheduler():

    __jobstore = {'default':SQLAlchemyJobStore("sqlite:///hector.sqlite")}
    __job_defaults = {'misfire_grace_time':None,'coalesce':True}
    apscheduler = QtScheduler(jobstores=__jobstore,job_defaults=__job_defaults)
    notifier = ToastNotifier()

    def __init__(self):
        self.jobs = self.apscheduler.get_jobs()
        self.apscheduler.start()
    
    def defaultFunc(self, title: str, msg: str):
        self.notifier.show_toast(title=title, msg=msg, duration=10, threaded=True)

    def add_date_job(self, date, name: str, desc: str, repeating: bool=False, weeks=None, days=None, hours=None, minutes=None, seconds=None):
        if(repeating): 
            self.apscheduler.add_job(self.defaultFunc, "interval", [name, desc], name=name, start_date=date, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        else: 
            self.apscheduler.add_job(self.defaultFunc, "date", [name, desc], name=name, run_date=date)

    def modify_job(self, job_id, name, desc, date, repeating=None, weeks=None, days=None, hours=None, minutes=None, seconds=None):
        self.apscheduler.modify_job(job_id, name=name, args = [self, name, desc])
        if(repeating):
            self.apscheduler.reschedule_job(job_id, trigger="interval", start_date=date, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        else:
            self.apscheduler.reschedule_job(job_id, trigger="date", run_date=date)

    def get_job(self, job_id):
        return self.apscheduler.get_job(job_id)
    
    def get_jobs(self, date=None):
        """
        Returns an dictionary that contains all necessary informain about the job for the program
        Attributes include (Name:str, Description:str, Type:str, Date:str, __date:datetime.datetime)
        All attributes that start with dunderscores are not strings, therefore should be skipped when being showed to the user.
        """
        arr = list()
        self.jobs = self.apscheduler.get_jobs()
        for x in self.jobs:
            job = dict()
            job['Name'] = x.name
            job['Description'] = x.args[2]
            try:
                date_run:datetime = x.next_run_time
                date_run = date_run.replace(microsecond=0)
                job["Type"] = "interval"
                job["__date"] = date_run
                job["Date"] = date_run.strftime("%a %#d %b %Y %r")
                job["Interval"] = x.trigger.interval
            except:
                    date_run:datetime = x.trigger.run_date
                    date_run = date_run.replace(microsecond=0)
                    job["Type"] = "date"
                    job["__date"] = date_run
            job["id"] = x.id
            if(date != None):
                target_date = datetime.combine(date, datetime.max.time()).replace(tzinfo=ZoneInfo("Asia/Bangkok"))
                if((job['Type'] == "interval") and (target_date > job['__date'])):
                    if(((target_date - job['__date'] + job['Interval']) % job['Interval']) > timedelta(days=1)):
                        continue
                    else:
                        while(target_date.date() > date_run.date()):
                            date_run = date_run + job['Interval']
                            if(date_run.date() == target_date.date()):
                                job["Date"] = date_run.strftime("%a %#d %b %Y %r")
                if(job['Type'] == "date"):
                    if(job['__date'].date() != date):
                        continue
            arr.append(job)
        return arr