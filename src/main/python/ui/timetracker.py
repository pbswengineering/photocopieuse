# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime
import logging
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import (
    QCalendarWidget,
    QProgressBar,
    QPushButton,
    QWidget,
    QApplication,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

from config import HelperType
from organization import Organization
from service.timetracker import Timetracker
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class TimetrackerUI(AbstractUI):

    organization: Organization
    _widget: Optional[QWidget]
    calendar: QCalendarWidget
    progress: QProgressBar
    pb_download: QPushButton
    pb_close: QPushButton
    webview: QWebEngineView

    signal_progress = QtCore.pyqtSignal(int, int)
    signal_success = QtCore.pyqtSignal(str)
    signal_failure = QtCore.pyqtSignal(str)

    def __init__(
        self,
        context: AbstractContext,
        organization: Organization,
        helper: HelperType,
        qapp: QApplication,
    ):
        super().__init__(qapp, context)
        self.context = context
        self.organization = organization
        self.helper = helper
        self._widget = None

    def widget(self) -> QWidget:
        if not self._widget:
            self._widget = uic.loadUi(self.context.get_resource("ui/timetracker.ui"))
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.calendar = self._widget.findChild(QCalendarWidget, "calendar")
            self.calendar.setLocale(QLocale(QLocale.English, QLocale.UnitedKingdom))
            self.progress = self._widget.findChild(QProgressBar, "progress")
            self.pb_download = self._widget.findChild(QPushButton, "pbDownload")
            self.pb_download.clicked.connect(self.pb_download_clicked)
            self.webview = QWebEngineView(self._widget)
            self._widget.layout().addWidget(self.webview)
            self.signal_success.connect(self.success)
            self.signal_progress.connect(self.show_progress)
        return self._widget

    def active(self, state):
        self.calendar.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_download.setEnabled(state)
        self.webview.setEnabled(state)

    def pb_download_clicked(self):
        self.active(False)
        self.context.show_status("Download in progress...")
        try:
            date = self.calendar.selectedDate().toPyDate()
        except Exception as e:
            logging.error(e)
            self.message_error("The date is incorrect")
            return
        TimetrackerTask(self, date).start()

    def success(self, html: str):
        self.active(True)
        self.webview.setHtml(html)
        self.context.clear_status()

    def show_progress(self, value: int, max_value: int):
        self.progress.setValue(value)
        self.progress.setMaximum(max_value)


class TimetrackerTask(BaseTask):
    ui: TimetrackerUI
    date: datetime

    def __init__(self, ui: TimetrackerUI, date: datetime):
        super().__init__()
        self.ui = ui
        self.date = date

    def run(self):
        try:
            timetracker = Timetracker(self.ui.organization, self.ui.helper)
            worklogs = timetracker.get_worklogs(self.date, self.ui.signal_progress)
            html = timetracker.worklogs_to_html(worklogs)
            self.ui.signal_success.emit(html)
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
