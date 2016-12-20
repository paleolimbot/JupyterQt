
from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDockWidget, QPlainTextEdit
from PyQt5.QtWebKitWidgets import QWebView, QWebPage

from logger import log

SETTING_GEOMETRY = "net.fishandwhistle/JupyterQt/geometry"


class LoggerDock(QDockWidget):

    def __init__(self, *args):
        super(LoggerDock, self).__init__(*args)
        self.textview = QPlainTextEdit(self)
        self.setWidget(self.textview)

    @pyqtSlot(str)
    def log(self, message):
        self.textview.appendPlainText(message)


class CustomWebView(QWebView):

    def __init__(self, mainwindow, main=False):
        super(CustomWebView, self).__init__(None)
        self.parent = mainwindow
        self.main = main
        self.loadedPage = None
        self.loadFinished.connect(self.onpagechange)

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        log("on page change: %s, %s" % (self.url(), ok))
        if self.loadedPage is not None:
            log("disconnecting on close and linkclicked signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
            self.loadedPage.linkClicked.disconnect(self.handlelink)

        log("connecting on close and linkclicked signal")
        self.loadedPage = self.page()
        self.loadedPage.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.loadedPage.windowCloseRequested.connect(self.close)
        self.loadedPage.linkClicked.connect(self.handlelink)
        self.setWindowTitle(self.title())
        if not ok:
            QMessageBox.information(self, "Error", "Error loading page!", QMessageBox.Ok)

    @pyqtSlot(QUrl)
    def handlelink(self, url):
        urlstr = url.toString()
        log("handling link : %s" % urlstr)
        # check if url is for the current page
        if url.matches(self.url(), QUrl.RemoveFragment):
            # do nothing, probably a JS link
            return True

        # check other windows to see if url is loaded there
        for window in self.parent.windows:
            if url.matches(window.url(), QUrl.RemoveFragment):
                window.raise_()
                window.activateWindow()
                # if this is a tree window and not the main one, close it
                if self.url().toString().startswith(self.parent.homepage + "tree") and not self.main:
                    QTimer.singleShot(0, self.close) # calling self.close() is no good
                return True

        if "/files/" in urlstr:
            # save, don't load new page
            self.parent.savefile(url)
        elif "/tree/" in urlstr or urlstr.startswith(self.parent.homepage + "tree"):
            # keep in same window
            self.load(url)
        else:
            # open in new window
            newwindow = self.createWindow(QWebPage.WebBrowserWindow, js=False)
            newwindow.load(url)

            # if this is a tree window and not the main one, close it
        if self.url().toString().startswith(self.parent.homepage + "/tree") and not self.main:
            QTimer.singleShot(0, self.close) # calling self.close() is no good
        return True

    def createWindow(self, windowtype, js=True):
        v = CustomWebView(self.parent)
        windows = self.parent.windows
        windows.append(v)
        cur = self.pos()
        # offset window slightly from current
        v.setGeometry(cur.x()+40, cur.y()+40, self.width(), self.height())
        log("Window count: %s" % (len(windows)+1))
        v.show()
        return v

    def closeEvent(self, event):
        if self.loadedPage is not None:
            log("disconnecting on close and linkClicked signals")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
            self.loadedPage.linkClicked.disconnect(self.handlelink)

        if not self.main:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            log("Window count: %s" % (len(self.parent.windows)+1))
        event.accept()


class MainWindow(QMainWindow):

    def __init__(self, parent=None, homepage=None):
        super(MainWindow, self).__init__(parent)
        self.homepage = homepage
        self.windows = []

        self.loggerdock = LoggerDock("Log Message", self)
        self.addDockWidget(Qt.BottomDockWidgetArea , self.loggerdock)

        settings = QSettings()
        val = settings.value(SETTING_GEOMETRY, None)
        if val is not None:
            self.restoreGeometry(val)

        self.basewebview = CustomWebView(self, main=True)
        self.setCentralWidget(self.basewebview)

    def loadmain(self, homepage):
        self.homepage = homepage
        QTimer.singleShot(0, self.initialload)

    @pyqtSlot()
    def initialload(self):
        if self.homepage:
            self.basewebview.load(QUrl(self.homepage))
        self.show()

    def savefile(self, url):
        pass

    def closeEvent(self, event):
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

        # save geometry
        settings = QSettings()
        settings.setValue(SETTING_GEOMETRY, self.saveGeometry())
