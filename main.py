

import sys
import os

from PyQt5.QtCore import QSettings, QDir, QObject, pyqtSignal, QUrl
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from logger import log, setup_logging, set_logger
from gui import MainWindow
from notebook_process import testnotebook, startnotebook, stopnotebook

SETTING_BASEDIR = "net.fishandwhistle/JupyterQt/basedir"
SETTING_EXECUTABLE = "net.fishandwhistle/JupyterQt/executable"
DEBUG = True

# setup application
app = QApplication(sys.argv)
app.setApplicationName("JupyterQt")
app.setOrganizationDomain("fishandwhistle.net")

s = QSettings()
execname = s.value(SETTING_EXECUTABLE, "jupyter-notebook")
if not testnotebook(execname):
    while True:
        QMessageBox.information(None, "Error", "It appears that Jupyter Notebook isn't where it usually is. " +
                                "Ensure you've installed Jupyter correctly and then press Ok to " +
                                "find the executable 'jupyter-notebook'", QMessageBox.Ok)
        if testnotebook(execname):
            break
        execname = QFileDialog.getOpenFileName(None, "Find jupyter-notebook executable", QDir.homePath())
        if not execname:
            # user hit cancel
            sys.exit(0)
        else:
            execname = execname[0]
            if testnotebook(execname):
                log("Jupyter found at %s" % execname)
                #save setting
                s.setValue(SETTING_EXECUTABLE, execname)
                break

# setup logging
# try to write to a log file, or redirect to stdout if debugging
logfile = os.path.join(str(QDir.homePath()), ".JupyterQt", "JupyterQt.log")
if not os.path.isdir(os.path.dirname(logfile)):
    os.mkdir(os.path.dirname(logfile))
try:
    if DEBUG:
        raise IOError()  # force logging to console
    f = open(logfile, "a")
    f.close()
    setup_logging(logfile)
except IOError:
    # no writable directory, log to console
    setup_logging(None)

log("Setting home directory...")
directory = None
file = None

if len(sys.argv) > 1:
    directory = sys.argv[-1]
    if os.path.isdir(directory):
        pass
    elif os.path.isfile(directory):
        file = os.path.basename(directory)
        directory = os.path.dirname(directory)
    else:
        # file not found
        QMessageBox.information(None, "Error", "The file/directory %s was not found" % directory, QMessageBox.Ok)
        directory = s.value(SETTING_BASEDIR, QDir.homePath())
else:
    directory = s.value(SETTING_BASEDIR, QDir.homePath())


log("Setting up GUI")
# setup webview
view = MainWindow(None, None)
view.setWindowTitle("JupyterQt: %s" % directory)

# redirect logging to view.loggerdock.log
class QtLogger(QObject):
    newlog = pyqtSignal(str)

    def __init__(self, parent):
        super(QtLogger, self).__init__(parent)

qtlogger = QtLogger(view)
qtlogger.newlog.connect(view.loggerdock.log)
set_logger(lambda message: qtlogger.newlog.emit(message))

# start the notebook process
webaddr = startnotebook(execname, directory=directory)
view.loadmain(webaddr)

# if notebook file is trying to get opened, open that window as well
if file is not None and file.endswith('.ipynb'):
    view.basewebview.handlelink(QUrl(webaddr + 'notebooks/' + file))
elif file is not None and file.endswith('.jproj'):
    pass
elif file is not None:
    # unrecognized file type
    QMessageBox.information(None, "Error", "File type of %s was unrecognized" % file, QMessageBox.Ok)

log("Starting Qt Event Loop")
result = app.exec_()

# resume regular logging
setup_logging(logfile)

# stop the notebook process
stopnotebook()

log("Exited.")
sys.exit(result)