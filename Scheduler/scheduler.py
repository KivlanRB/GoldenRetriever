from win10toast import ToastNotifier
from apscheduler.schedulers.qt import QtScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from zoneinfo import ZoneInfo
from datetime import date, datetime, timedelta
from time import sleep

class Scheduler():

    __jobstore = {'default':SQLAlchemyJobStore("sqlite:///hector.sqlite")}
    __job_defaults = {'misfire_grace_time':None,'coalesce':True}
    __debug = True
    apscheduler = QtScheduler(jobstores=__jobstore,job_defaults=__job_defaults)
    notifier = ToastNotifier()

    def __init__(self):
        self.apscheduler.start()
        self.jobs = self.apscheduler.get_jobs()
    
    def __job_to_dict(self, x):
        job = dict()
        if x.name.find("@") != -1:
            job['__source'] = x.name[x.name.find("@")+1:]
            job['Name'] = x.name[:x.name.find("@")]
        else:    
            job['Name'] = x.name
        job['Description'] = x.args[2]
        try:
            date_run:datetime = x.next_run_time
            date_run = date_run.replace(microsecond=0)
            job["Type"] = "interval"
            job["__date"] = date_run
            job["Date"] = date_run.strftime("%a %#d %b %Y %r")
            job["Interval"] = x.trigger.interval
        except AttributeError:
                date_run:datetime = x.trigger.run_date
                date_run = date_run.replace(microsecond=0)
                job["Type"] = "date"
                job["__date"] = date_run
        job["id"] = x.id
        
        return job
    
    def defaultFunc(self, title: str, msg: str):
        if self.__debug:
            print("Job executed at {}".format(datetime.now()))
        self.notifier.show_toast(title=title, msg=msg, duration=10, threaded=True)
    
    def refresh(self):
        self.jobs = self.apscheduler.get_jobs()

    def add_date_job(self, date, name: str, desc: str, repeating: bool=False, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        if(repeating): 
            self.apscheduler.add_job(self.defaultFunc, "interval", [name, desc], name=name, start_date=date, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        else: 
            self.apscheduler.add_job(self.defaultFunc, "date", [name, desc], name=name, run_date=date)

    def modify_job(self, job_id, name, desc, date, repeating: bool=False, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        self.apscheduler.modify_job(job_id, name=name, args = [self, name, desc])
        if(repeating):
            self.apscheduler.reschedule_job(job_id, trigger="interval", start_date=date, weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        else:
            self.apscheduler.reschedule_job(job_id, trigger="date", run_date=date)

    def get_job(self, job_id) -> dict:
        job = self.apscheduler.get_job(job_id)
        if(not job):
            return
        return self.__job_to_dict(job)

    
    def get_jobs(self, date=None):
        """
        Returns an dictionary that contains all necessary informain about the job for the program
        Attributes include (Name:str, Description:str, Type:str, Date:str, __date:datetime.datetime)
        All attributes that start with dunderscores are not strings, therefore should be skipped when being showed to the user.
        """
        arr = list()
        for x in self.jobs:
            job = self.__job_to_dict(x)
            if(date != None):
                target_date = datetime.combine(date, datetime.max.time()).replace(tzinfo=ZoneInfo("Asia/Bangkok"))
                if((job['Type'] == "interval")):
                    if(target_date > job['__date']):
                        if(((target_date - job['__date'] + job['Interval']) % job['Interval']) > timedelta(days=1)):
                            continue
                        else:
                            while(target_date.date() > job['__date'].date()):
                                job['__date'] = job['__date'] + job['Interval']
                                if(job['__date'].date() == target_date.date()):
                                    job["Date"] = job['__date'].strftime("%a %#d %b %Y %r")
                    else:
                        continue
                if(job['Type'] == "date"):
                    if(job['__date'].date() != date):
                        continue
            arr.append(job)
        return arr
    
    def remove_job(self, id):
        self.apscheduler.remove_job(id)

if __name__ == '__main__':
    sched = Scheduler()
    sched.add_date_job(datetime.now()+timedelta(seconds=10), "test", "test")
    job = sched.get_jobs()[0]
    print(job)
    sleep(5)
    sched.modify_job(job['id'], "Hello!", "World!", job['__date']+timedelta(seconds=10))
    job = sched.get_jobs()[0]
    print(job)
    sleep(21)