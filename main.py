

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
import time



app = QApplication(sys.argv)
app.setApplicationName("JupyterQt")
app.setOrganizationDomain("fishandwhistle.net")

#start jupyter notebook
def startnotebook(port=8888, directory="~"):
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

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        if self.loadedPage is not None:
            print("disconnecting on close signal signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
        self.loadedPage = self.page()
        print("connecting on close signal")
        self.loadedPage.windowCloseRequested.connect(self.close)
        self.setWindowTitle(self.title())

    def createWindow(self, windowtype):
        v = CustomWebView(self if self.parent is None else self.parent)
        windows = self.windows if self.parent is None else self.parent.windows
        windows.append(v)
        v.show()
        print("Window count: self + %s" % (len(windows)+1))
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
            else:
                event.accept()
        else:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            print("Window count: self + %s" % (len(self.parent.windows)+1))
            event.accept()

#start notebook
notebookp = startnotebook()

#setup webview
view = CustomWebView()
time.sleep(3) #let server get setup, isn't always long enough
view.load(QUrl("http://localhost:8888/"))
view.show()
result = app.exec_()

notebookp.terminate()
sys.exit(result)