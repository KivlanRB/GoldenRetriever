from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from dateutil import rrule
from GUI.main_gui import Ui_MainWindow
from GUI.joblist_gui import Ui_Dialog as Ui_JobList
from GUI.editjob_gui import Ui_Dialog as Ui_EditJob
from GUI.emasinput_gui import Ui_Dialog as Ui_EmasInput
from GUI.loading_gui import Ui_Dialog as Ui_Loading
from Scheduler.scheduler import Scheduler
from API.storesafe import StoreSafe
from API.emas import EmasAPI
from API.gcalendar import GoogleAPI
from typing import Union
from os import path
import datetime, qdarkstyle


class GoldenRetriever(QMainWindow):
    def __init__(self) -> None:
        self.obj_scheduler = Scheduler()
        self.store = StoreSafe("GoldenRetriever")
        super().__init__()
        if path.exists(path.join("rsc", "main.ico")):
            self.__icon = QIcon(path.join("rsc", "main.ico"))
        else:
            print("Unable to find the app icon!\nUsing default OS Icon.")
            self.__icon = QIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.__icon)
        self._toggle_show_action = QAction("Show", self)
        self._quit_action = QAction("Quit", self)
        self._toggle_show_action.triggered.connect(lambda: self.show() if self.isHidden() else self.setFocus())
        self._quit_action.triggered.connect(qApp.quit)
        self._menu = QMenu()
        self._menu.addAction(self._toggle_show_action)
        self._menu.addAction(self._quit_action)
        self.tray.setContextMenu(self._menu)
        self.tray.activated.connect(lambda reason: self.__clicked_reason(reason, lambda: self.show() if self.isHidden() else None))
        self.tray.show()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(self.__icon)
        self.setWindowTitle("GoldenRetriever")
        self.ui.dateTimeEdit.setDateTime(datetime.datetime.now())
        self.ui.manualJobAddBtn.clicked.connect(self.addManualJob)
        self.ui.calendarWidget.activated.connect(lambda: self.openListJobView(self.ui.calendarWidget.selectedDate().toPyDate()))
        self.ui.hm_JobsListViewBtn.clicked.connect(lambda: self.openListJobView())
        self.ui.nw_JobListViewBtn.clicked.connect(lambda: self.openListJobView())
        self.ui.hm_jobTreeWidget.itemActivated.connect(self.editJob)
        self.ui.hm_refreshBtn.clicked.connect(self.refresh)
        self.ui.nw_refreshBtn.clicked.connect(self.refresh)
        self.ui.nw_jobTreeWidget.itemActivated.connect(self.editJob)
        self.ui.uiSyncBtn.clicked.connect(self._emas_login)
        self.ui.gcalendarSyncBtn.clicked.connect(self._google_loading)
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        self.__setup_tree_views()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.ui.trayRadioBtn.isChecked():    
            event.ignore()
            self.hide()
            self.tray.showMessage("GoldenRetriever", 
            "Application was minimized to tray.", 
            QSystemTrayIcon.Information, 2000)
        else:
            return super().closeEvent(event)
        
    def __clicked_reason(self, reason, func):
        if reason == QSystemTrayIcon.DoubleClick:
            func()
        
    def __setup_tree_views(self):
        now = datetime.datetime.now()
        jobs = list()

        for weekday in rrule.rrule(rrule.DAILY, dtstart=now, until=now + datetime.timedelta(weeks=1)):
            weekday = weekday.date()
            for job in self.jobs_to_treeview(weekday):
                jobs.append(job)
        self.ui.hm_jobTreeWidget.invisibleRootItem().addChildren(jobs)

        for weekday in rrule.rrule(rrule.DAILY, dtstart=now + datetime.timedelta(weeks=1), until=now + datetime.timedelta(weeks=2)):
            weekday = weekday.date()
            for job in self.jobs_to_treeview(weekday):
                jobs.append(job)
        self.ui.nw_jobTreeWidget.invisibleRootItem().addChildren(jobs)
    
    def __keyring_store(self, un:str, pw:str):
        self.store._set_creds(un, pw)
        self._emas_loading(un, pw)
    
    def _emas_login(self):
        uname, pword = self.store._get_creds()
        if (not uname) or (not pword):
            dig = EmasInputWindow(self)
            dig.gotCreds.connect(self.__keyring_store)
            dig.show()
        else:
            self._emas_loading(uname, pword)

    def _emas_loading(self, un:str, pw:str):
        loading = LoadingWindow(self)
        self._worker = EmasWorker(un, pw)
        self._thread = QThread()
        self._worker.finished.connect(lambda res, arr: self._site_integration(res, arr, "emas"))
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(loading.close)
        self._thread.started.connect(self._worker.main)
        self._thread.start()
        loading.show()
    
    def _site_integration(self, success, deadlines, source):
        if not success:
            self.store._delete_creds()
            QMessageBox.critical(self, "Error!", deadlines[0])
            return
        for job in self.obj_scheduler.get_jobs():
            try:
                if job['__source'] == source:
                    self.obj_scheduler.remove_job(job['id'])
            except KeyError:
                continue
        for deadline in deadlines:
            name = deadline['name'] + "@" + source
            date = deadline['date']
            if date < datetime.datetime.now():
                continue
            try:
                desc = deadline['desc']
            except KeyError:
                desc = ""
            self.obj_scheduler.add_date_job(date, name, desc)
        self.refresh()
    
    def _google_loading(self):
        loading = LoadingWindow(self)
        self._thread = QThread()
        self._worker = GCalendarWorker()
        self._worker.finished.connect(lambda res, arr: self._site_integration(res, arr, "google"))
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(loading.close)
        self._thread.started.connect(self._worker.main)
        self._thread.start()
        loading.show()

    def QTreeWidgetItem_to_JobID(self, item:QTreeWidgetItem) -> Union[str, None]:
        job_id:str = None
        if (item.childCount()):
            job_id = item.child(item.childCount()-1).text(0)
        else:
            parent = item.parent()
            job_id = parent.child(parent.childCount()-1).text(0)
        
        return job_id[job_id.find(" ")+1:] if job_id.startswith("id: ") else None
    
    def refresh(self):
        self.obj_scheduler.refresh()
        self.ui.nw_jobTreeWidget.clear()
        self.ui.hm_jobTreeWidget.clear()
        self.__setup_tree_views()
    
    def editJob(self, job:QTreeWidgetItem):
        job_id = self.QTreeWidgetItem_to_JobID(job)
        if (not job_id):
            QMessageBox.critical(self, "Error!", 
            """There was an error in trying to get the event's ID!
Screenshot the program and send it to the devs for further investigation!
            """)
            return
        
        editJob = editJobWindow(self, job_id)
        editJob.setWindowTitle("Edit job")
        editJob.show()
    
    def jobs_to_treeview(self, date=None):
        jobs = self.obj_scheduler.get_jobs(date)
        tree_items = list()
        for job in jobs:
            parent = QTreeWidgetItem([job['Name']])
            for key in job.keys():
                if key.startswith("__"):
                    continue
                parent.addChild(QTreeWidgetItem([key + ": " + str(job[key])]))
            tree_items.append(parent)
        
        return tree_items
    
    def openListJobView(self, date:datetime.date=None):
        jobList = jobListWindow(self, date)
        jobList.show()

    def addManualJob(self):
        name = self.ui.jobNameEdit.text()
        desc = self.ui.jobDescEdit.toPlainText()
        date = self.ui.dateTimeEdit.dateTime().toPyDateTime()

        if (name.find("@") != -1) or (name.find("&") != -1) or (name.find(":") != -1):
            QMessageBox.critical(self, "Error!", "The name of an event cannot have ampersands (&) or at signsW (@) or colons (:)")
            return
        
        if self.ui.IntervalRadioBtn.isChecked():
            seconds = self.ui.secondsSpinBox.value()
            minutes = self.ui.minutesSpinBox.value()
            hours = self.ui.hoursSpinBox.value()
            days = self.ui.daysSpinBox.value()
            weeks = self.ui.weeksSpinBox.value()
            try:
                self.obj_scheduler.add_date_job(date, 
                                                name, 
                                                desc, 
                                                repeating=True,
                                                weeks=weeks, 
                                                days=days, 
                                                hours=hours, 
                                                minutes=minutes, 
                                                seconds=seconds)
            except Exception as e:
                QMessageBox.critical(self, "Error!", "There was an error adding a job!\n\n{}".format(e))
                return
        else:
            try:
                self.obj_scheduler.add_date_job(date, name, desc)
            except Exception as e:
                QMessageBox.critical(self, "Error!", "There was an error adding a job!\n\n{}".format(e))
                return
        self.refresh()
        QMessageBox.information(self, "Info", "Job added!")
        

class jobListWindow(QDialog):

    def __init__(self, parent, date:datetime.date) -> None:
        super().__init__(parent=parent)
        self.ui = Ui_JobList()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)

        self.date = date
        self.setWindowTitle("Event list")
        self.ui.treeWidget.invisibleRootItem().addChildren(self.parent().jobs_to_treeview(self.date))
        self.ui.treeWidget.itemActivated.connect(self.editJob)
    
    def refresh(self):
        self.ui.treeWidget.clear()
        self.ui.treeWidget.invisibleRootItem().addChildren(self.parent().jobs_to_treeview(self.date))
        self.parent().refresh()
    
    def editJob(self, job:QTreeWidgetItem):
        job_id = self.parent().QTreeWidgetItem_to_JobID(job)
        if (not job_id):
            QMessageBox.critical(self, "Error!", 
            """There was an error in trying to get the event's ID!
Screenshot the program and send it to the devs for further investigation!
            """)
            return
        
        editJob = editJobWindow(self, job_id)
        editJob.setWindowTitle("Edit job")
        editJob.show()

class editJobWindow(QDialog):
    def __init__(self, parent, job_id) -> None:
        super().__init__(parent=parent)
        self.ui = Ui_EditJob()
        self.ui.setupUi(self)
        self.job_id = job_id
        self.setWindowModality(Qt.ApplicationModal)

        try:
            self.sched = parent.obj_scheduler
            self.job = self.sched.get_job(self.job_id)
        except AttributeError:
            try:
                self.sched = parent.parent().obj_scheduler
                self.job = self.sched.get_job(self.job_id)
            except:
                QMessageBox.critical(self, "Error!", "Could not reach the scheduler!")
                self.close()
                return
        if self.job['Type'] == 'interval':
            total_seconds = self.job['Interval'].total_seconds()
            seconds = int(total_seconds % 60)
            minutes = int(total_seconds // 60 % 60)
            hours = int(total_seconds // 3600 % 2)
            days = int(total_seconds // 86400 % 7)
            weeks = int(total_seconds // (86400*7))
            self.ui.secondsSpinBox.setValue(seconds)
            self.ui.minutesSpinBox.setValue(minutes)
            self.ui.hoursSpinBox.setValue(hours)
            self.ui.daysSpinBox.setValue(days)
            self.ui.weeksSpinBox.setValue(weeks)
            self.ui.IntervalRadioBtn.setChecked(True)
        self.ui.jobNameEdit.setText(self.job['Name'])
        self.ui.jobDescEdit.setText(self.job['Description'])
        self.ui.dateTimeEdit.setDateTime(self.job['__date'])

        self.ui.manualJobEditBtn.clicked.connect(self.editJob)
        self.ui.deleteJobBtn.clicked.connect(self.remove_job)

    def editJob(self):
        try:
            name = self.ui.jobNameEdit.text()
            desc = self.ui.jobDescEdit.toPlainText()
            date = self.ui.dateTimeEdit.dateTime().toPyDateTime()
            if not self.ui.IntervalRadioBtn.isChecked():
                self.sched.modify_job(self.job_id, name, desc, date)
            else:
                seconds = self.ui.secondsSpinBox.value()
                minutes = self.ui.minutesSpinBox.value()
                hours = self.ui.hoursSpinBox.value()
                days = self.ui.daysSpinBox.value()
                weeks = self.ui.weeksSpinBox.value()
                self.sched.modify_job(self.job_id, 
                                            name, 
                                            desc, 
                                            date,
                                            repeating=True,
                                            seconds=seconds,
                                            minutes=minutes,
                                            hours=hours,
                                            days=days,
                                            weeks=weeks)
        except Exception as e:
            QMessageBox.critical(self, "Error!", "There was an error adding a job!\n\n{}".format(e))
            return
        QMessageBox.information(self, "Job modified!", "Job successfully modified!")
        self.parent().refresh()
        self.close()
    
    def remove_job(self):
        try:
            self.sched.remove_job(self.job_id)
            QMessageBox.information(self, "Success!", "Job removed!")
            self.parent().refresh()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error!", f"There was an error in removing the event!\n{e}")
            self.parent().refresh()
            self.close()
        

class EmasInputWindow(QDialog):

    gotCreds = pyqtSignal(str, str)

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.ui = Ui_EmasInput()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui.submitBtn.clicked.connect(self.submit)
    
    def submit(self):
        self.gotCreds.emit(self.ui.unameEdit.text(), self.ui.pwordEdit.text())
        self.close()

class LoadingWindow(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.ui = Ui_Loading()
        self.ui.setupUi(self)
        self.setWindowTitle("Loading...")
        if path.exists(path.join("rsc", "loading.gif")):
            self.movie = QMovie(path.join("rsc", "loading.gif"))
            self.ui.label.setMovie(self.movie)
            self.movie.start()
        else:
            print("Unable to find the loading gif!")
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

class EmasWorker(QObject):
    finished = pyqtSignal(bool, list)

    def __init__(self, un, pw) -> None:
        super().__init__()
        self.uname = un
        self.pword = pw

    @pyqtSlot()
    def main(self):
        try:
            eapi = EmasAPI(debug=False)
        except OSError:
            self.finished.emit(False, ["Error loading firefox driver.\nPlease install the latest version of firefox!"])
            return
        eapi.login(self.uname, self.pword)
        res, msg = eapi.emas_login()
        if res == 1:
            self.arr = eapi.get_timeline()
            eapi.close()
            self.finished.emit(True, self.arr)
        else:
            eapi.close()
            self.finished.emit(False, [msg])

class GCalendarWorker(QObject):
    finished = pyqtSignal(bool, list)

    def __init__(self) -> None:
        super().__init__()
        
    @pyqtSlot()
    def main(self):
        gcli = GoogleAPI()
        gcli.login()
        self.arr = gcli.GetTask()
        self.finished.emit(True, self.arr)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    ui = GoldenRetriever()
    ui.show()
    sys.exit(app.exec_())
