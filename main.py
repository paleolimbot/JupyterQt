

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView

import sys
import os
import subprocess
import signal
import logging
import threading

SETTING_BASEDIR = "net.fishandwhistle/JupyterQt/basedir"
SETTING_GEOMETRY = "net.fishandwhistle/JupyterQt/geometry"
SETTING_EXECUTABLE = "net.fishandwhistle/JupyterQt/executable"

logging.basicConfig(level=logging.DEBUG, filename="jupyterQt.log",
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s')


def log(message):
    logging.debug(message)


#setup application
app = QApplication(sys.argv)
app.setApplicationName("JupyterQt")
app.setOrganizationDomain("fishandwhistle.net")

class CustomWebView(QWebView):

    def __init__(self, parent=None):
        super(CustomWebView, self).__init__(None)
        self.parent = parent
        if parent is None:
            self.windows = []
        self.loadedPage = None
        self.loadFinished.connect(self.onpagechange)

        settings = QSettings()
        val = settings.value(SETTING_GEOMETRY, None)
        if val is not None:
            self.restoreGeometry(val)

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        if self.loadedPage is not None:
            log("disconnecting on close signal signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
        self.loadedPage = self.page()
        log("connecting on close signal")
        self.loadedPage.windowCloseRequested.connect(self.close)
        #self.loadedPage.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.setWindowTitle(self.title())
        if not ok:
            QMessageBox.information(self, "Error", "Error loading page!", QMessageBox.Ok)
            self.back()

    def createWindow(self, windowtype):
        v = CustomWebView(self if self.parent is None else self.parent)
        windows = self.windows if self.parent is None else self.parent.windows
        windows.append(v)
        cur = self.pos()
        #offset window slightly from current
        v.setGeometry(cur.x()+40, cur.y()+40, self.width(), self.height())
        v.show()
        log("Window count: %s" % (len(windows)+1))

        return v

    def closeEvent(self, event):
        if self.loadedPage is not None:
            log("disconnecting on close signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)

        if self.parent is None:
            if self.windows:
                if QMessageBox.Ok == QMessageBox.information(self,
                                                         "Really Close?",
                                                         "Really close %s windows?" % (len(self.windows)+1),
                                                         QMessageBox.Cancel | QMessageBox.Ok):
                    for i in reversed(range(len(self.windows))):
                        w = self.windows.pop(i)
                        w.close()
                    event.accept()
                else:
                    event.ignore()
                    return
            else:
                event.accept()

            #save geometry
            settings = QSettings()
            settings.setValue(SETTING_GEOMETRY, self.saveGeometry())
        else:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            log("Window count: %s" % (len(self.parent.windows)+1))
            event.accept()

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.basewebview = None

#notebook subprocess stuff
def testnotebook(notebook_executable="jupyter-notebook"):
    return 0 == os.system("%s --version" % notebook_executable)

def startnotebook(notebook_executable="jupyter-notebook", port=8888, directory=QDir.homePath()):
    return subprocess.Popen(["jupyter-notebook",
                            "--port=%s" % port, "--browser=n", "-y",
                            "--notebook-dir=%s" % directory], bufsize=1,
                            stderr=subprocess.PIPE)

#start notebook
log("starting application...")

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


log("Setting home directory...")
portnum = 8888
directory = s.value(SETTING_BASEDIR, QDir.homePath())
if not os.path.isdir(directory):
    log("Directory %s not found, defaulting to home directory" % directory)
    directory = QDir.homePath()

log("Starting Jupyter notebook process")
#start jupyter notebook and wait for line with the web address
notebookp = startnotebook(execname, portnum, directory)

log("Waiting for server to start...")
webaddr = None
while webaddr is None:
    line = str(notebookp.stderr.readline())
    log(line)
    if "http://" in line:
        start = line.find("http://")
        end = line.find("/", start+len("http://"))
        webaddr = line[start:end]

log("Server found at %s, migrating monitoring to listener thread" % webaddr)
#pass monitoring over to child thread
def process_thread_pipe(process):
    while process.poll() is None: #while process is still alive
        log(str(process.stderr.readline()))
    log("Final output:")
    log(process.communicate())

notebookmonitor = threading.Thread(name="Notebook Monitor", target=process_thread_pipe,
                                   args = (notebookp,), daemon=True)
notebookmonitor.start()

log("Setting up GUI")
#setup webview
view = CustomWebView()
view.load(QUrl(webaddr))
view.show()

log("Starting Qt Event Loop")
result = app.exec_()
log("Exiting..sending interrupt signal to jupyter-notebook")
notebookp.send_signal(signal.SIGINT)
try:
    log("Waiting for jupyter to exit...")
    notebookp.wait(10)
    log("Waiting for monitor thread to join...")
    notebookmonitor.join(10)
except TimeoutError:
    log("control c timed out, killing")
    notebookp.kill()

sys.exit(result)