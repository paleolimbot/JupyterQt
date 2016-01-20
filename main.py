

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView, QWebPage
from PyQt5.QtGui import QDesktopServices

#imports to keep dependencies in
import jupyter, jupyter_client, jupyter_console, jupyter_core
import numpy
import matplotlib

import sys
import subprocess
import signal
import time

SETTING_BASEDIR = "net.fishandwhistle/JupyterQt/basedir"
SETTING_GEOMETRY = "net.fishandwhistle/JupyterQt/geometry"

#setup application
app = QApplication(sys.argv)
app.setApplicationName("JupyterQt")
app.setOrganizationDomain("fishandwhistle.net")


def startnotebook(port=8888, directory=QDir.homePath()):
    return subprocess.Popen(["jupyter", "notebook",
                            "--port=%s" % port, "--browser=n", "-y",
                            "--notebook-dir=%s" % directory])


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
            print("disconnecting on close signal signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
        self.loadedPage = self.page()
        print("connecting on close signal")
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
        print("Window count: %s" % (len(windows)+1))

        return v

    def closeEvent(self, event):
        if self.loadedPage is not None:
            print("disconnecting on close signal")
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
            print("Window count: %s" % (len(self.parent.windows)+1))
            event.accept()

#start notebook
portnum = 8888
s = QSettings()
directory = QFileDialog.getExistingDirectory(None, "Choose a directory for Jupyter", s.value(SETTING_BASEDIR, QDir.homePath()))
if not directory:
    #user hit cancel
    print("User cancelled file dialog, closing.")
    sys.exit(0)

s.setValue(SETTING_BASEDIR, directory)
notebookp = startnotebook(portnum, directory)

#setup webview
view = CustomWebView()
time.sleep(3) #let server get setup, isn't always long enough
view.load(QUrl("http://localhost:%s/" % portnum))
view.show()
result = app.exec_()

notebookp.send_signal(signal.SIGINT)
try:
    print("Waiting for jupyter to exit...")
    notebookp.wait(10)
except TimeoutError:
    print("control c timed out, killing")
    notebookp.kill()

sys.exit(result)