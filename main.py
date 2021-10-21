from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from Scheduler.scheduler import Scheduler
from datetime import datetime
import sys

class main (QMainWindow):
    def __init__(self, parent=None):
        super(main, self).__init__(parent)
        loadUi("mainWindow.ui",self)
        self.setWindowTitle("GoldenRetriever")
        self.setAlarmButton.clicked.connect(lambda: self.setAlarm())
        self.dateTimeEdit.setDateTime(datetime.now())
        self.calendarWidget.activated.connect(lambda: self.viewJobOnDate())
        self.objScheduler = Scheduler()

    def setAlarm(self):
        name = self.jobNameEdit.text()
        desc = self.jobDescEdit.toPlainText()
        date = self.dateTimeEdit.dateTime().toPyDateTime()

        if self.jobIntervalTriggerButton.isChecked():
            seconds = self.secondsSpinBox.value()
            minutes = self.minutesSpinBox.value()
            hours = self.hoursSpinBox.value()
            days = self.daysSpinBox.value()
            weeks = self.weeksSpinBox.value()
            return self.objScheduler.add_date_job(date, name=name, desc=desc, repeating=True, seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
        else:
            return self.objScheduler.add_date_job(date, name=name, desc=desc)
        
    def viewJobOnDate(self):
        self.viewJobOnDateDialog = dateViewDialog(self)
        self.viewJobOnDateDialog.show()
        jobs = self.objScheduler.get_jobs(self.calendarWidget.selectedDate().toPyDate())
        for job in jobs:
            arr = list()
            for key in job.keys():
                if(key.startswith("__")):
                    continue
                arr.append("{}: {}".format(key, job[key]))
            self.viewJobOnDateDialog.jobListWidget.addItem("\n".join(arr))
        
class editJobDialog (QMainWindow):
    def __init__(self, job_id, parent: main=None):
        super(editJobDialog, self).__init__(parent)
        loadUi("editDialog.ui", self)
        self.job = parent.objScheduler.get_job(job_id)
        self.jobNameEdit.setText(self.job.name)
        self.jobDescEdit.setPlainText(self.job.args[2])
        self.jobIdEdit.setText(self.job.id)
        try:
            interval = self.job.trigger.interval
            weeks, days, hours, minutes, seconds = interval.days//7, interval.days, interval.seconds//3600, (interval.seconds//60)%60, interval.seconds%60
            print(seconds, minutes, hours, days, weeks)
            self.jobDateTimeEdit.setDateTime(self.job.trigger.start_date)
            self.secondsSpinBox.setValue(seconds)
            self.minutesSpinBox.setValue(minutes)
            self.hoursSpinBox.setValue(hours)
            self.daysSpinBox.setValue(days)
            self.weeksSpinBox.setValue(weeks)
            self.jobIntervalTriggerButton.setChecked(True)
        except AttributeError:
            self.jobDateTimeEdit.setDateTime(self.job.trigger.run_date)
        self.dialogButton.accepted.connect(self.saveJob)
        self.dialogButton.rejected.connect(lambda: self.close())
        self.setWindowTitle("Editting {} task".format(self.job.name))

    def saveJob(self):
        name = self.jobNameEdit.text()
        desc = self.jobDescEdit.toPlainText()
        date = self.jobDateTimeEdit.dateTime().toPyDateTime()

        if self.jobIntervalTriggerButton.isChecked():
            seconds = self.secondsSpinBox.value()
            minutes = self.minutesSpinBox.value()
            hours = self.hoursSpinBox.value()
            days = self.daysSpinBox.value()
            weeks = self.weeksSpinBox.value()
            self.parent().objScheduler.modify_job(self.job.id, date=date, name=name, desc=desc, repeating=True, seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
        else:
            self.parent().objScheduler.modify_job(self.job.id, date=date, name=name, desc=desc)
        
        self.close()
        
        

class dateViewDialog (QMainWindow):
    def __init__(self, parent: main=None):
        super(dateViewDialog, self).__init__(parent)
        loadUi("dateView.ui", self)
        self.jobListWidget.itemDoubleClicked.connect(self.editJob)
        self.setWindowTitle("List job")
    
    def editJob(self, item):
        job_id:str = item.text()
        job_id = job_id[job_id.find("id:")+4:]
        self.editJobDialog = editJobDialog(job_id, self.parent())
        self.editJobDialog.show()

app = QApplication([])
mainwindow = main()
app.setQuitOnLastWindowClosed(True)
mainwindow.show()
sys.exit(app.exec_())