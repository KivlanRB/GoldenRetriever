from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from Scheduler.scheduler import Scheduler
from datetime import datetime
import sys

class editDialog (QMainWindow):
    def __init__(self, parent=None):
        super(editDialog, self).__init__(parent)
        loadUi("editDialog.ui", self)
        self.setWindowTitle("Edit job")

class main (QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("mainWindow.ui",self)
        self.setWindowTitle("GoldenRetriever")
        self.setAlarmButton.clicked.connect(self.setAlarm)
        self.editJobButton.clicked.connect(self.editJob)
        self.dateTimeEdit.setDateTime(datetime.now())
        self.editJob = editDialog(self)
        self.obj_Scheduler = Scheduler()

    def setAlarm(self):
        date = self.dateTimeEdit.dateTime().toPyDateTime()
        self.obj_Scheduler.add_date_job(date, title="test", msg="This is a test alarm")

    def editJob(self, job):
        self.editJob.show()

app = QApplication([])
mainwindow = main()
app.setQuitOnLastWindowClosed(True)
mainwindow.show()
sys.exit(app.exec_())