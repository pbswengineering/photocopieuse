# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QDateEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTimeEdit,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.holidays import Holidays
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class HolidayUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    _widget: Optional[QWidget]
    tab_widget: QTabWidget
    de_p_day: QDateEdit
    te_p_beginning: QTimeEdit
    te_p_ending: QTimeEdit
    te_p_description: QPlainTextEdit
    de_d_day: QDateEdit
    te_d_description: QPlainTextEdit
    de_md_beginning: QDateEdit
    de_md_ending: QDateEdit
    te_md_description: QPlainTextEdit
    de_date: QDateEdit
    pb_close: QPushButton
    pb_schedule: QPushButton
    signal_success = QtCore.pyqtSignal()
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
            now = datetime.now()
            self._widget = uic.loadUi(self.context.get_resource("ui/holidays.ui"))
            self.tab_widget = self._widget.findChild(QTabWidget, "tabWidget")
            self.de_p_day = self._widget.findChild(QDateEdit, "dePDay")
            self.de_p_day.setDateTime(now)
            self.te_p_beginning = self._widget.findChild(QTimeEdit, "tePBeginning")
            self.te_p_beginning.setDateTime(now)
            self.te_p_ending = self._widget.findChild(QTimeEdit, "tePEnding")
            self.te_p_ending.setDateTime(now)
            self.te_p_description = self._widget.findChild(
                QPlainTextEdit, "tePDescription"
            )
            self.de_d_day = self._widget.findChild(QDateEdit, "deDDay")
            self.de_d_day.setDateTime(now)
            self.te_d_description = self._widget.findChild(
                QPlainTextEdit, "teDDescription"
            )
            self.de_md_beginning = self._widget.findChild(QDateEdit, "deMDBeginning")
            self.de_md_beginning.setDateTime(now)
            self.de_md_ending = self._widget.findChild(QDateEdit, "deMDEnding")
            self.de_md_ending.setDateTime(now)
            self.te_md_description = self._widget.findChild(
                QPlainTextEdit, "teMDDescription"
            )
            self.de_date = self._widget.findChild(QDateEdit, "deDate")
            self.de_date.setDateTime(now)
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_schedule = self._widget.findChild(QPushButton, "pbSchedule")
            self.pb_schedule.clicked.connect(self.pb_schedule_clicked)
            self.signal_failure.connect(self.failure)
            self.signal_success.connect(self.success)
        return self._widget

    def active(self, state: bool):
        self.tab_widget.setEnabled(state)
        self.de_p_day.setEnabled(state)
        self.te_p_beginning.setEnabled(state)
        self.te_p_ending.setEnabled(state)
        self.te_p_description.setEnabled(state)
        self.de_d_day.setEnabled(state)
        self.te_d_description.setEnabled(state)
        self.de_md_beginning.setEnabled(state)
        self.de_md_ending.setEnabled(state)
        self.te_md_description.setEnabled(state)
        self.de_date.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_schedule.setEnabled(state)

    def pb_schedule_clicked(self):
        request_type = self.tab_widget.currentIndex()
        # 0 - Permit
        p_day = self.de_p_day.dateTime().toPyDateTime()
        p_beginning = self.te_p_beginning.dateTime().toPyDateTime()
        p_ending = self.te_p_ending.dateTime().toPyDateTime()
        # 1 - Single day holiday
        d_day = self.de_d_day.dateTime().toPyDateTime()
        # 2 - Multiple days holiday
        md_beginning = self.de_md_beginning.dateTime().toPyDateTime()
        md_ending = self.de_md_ending.dateTime().toPyDateTime()
        if request_type == 0:
            description = self.te_p_description.toPlainText()
        elif request_type == 1:
            description = self.te_d_description.toPlainText()
        else:
            description = self.te_md_description.toPlainText()
        date = self.de_date.dateTime().toPyDateTime()
        self.active(False)
        self.context.show_status(
            "Creating the PDF request and updating the wiki page..."
        )
        HolidayTask(
            self,
            request_type,
            date,
            description,
            p_day,
            p_beginning,
            p_ending,
            d_day,
            md_beginning,
            md_ending,
        ).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info("The PDF has been created within the 'HOME' directory")


class HolidayTask(BaseTask):
    ui: HolidayUI
    request_type: int
    date: datetime
    description: str
    p_day: datetime
    p_beginning: datetime
    p_ending: datetime
    d_day: datetime
    md_beginning: datetime
    md_ending: datetime

    def __init__(
        self,
        ui: HolidayUI,
        request_type: int,
        date: datetime,
        description: str,
        p_day: datetime,
        p_beginning: datetime,
        p_ending: datetime,
        d_day: datetime,
        md_beginning: datetime,
        md_ending: datetime,
    ):
        super().__init__()
        self.ui = ui
        self.request_type = request_type
        self.date = date
        self.description = description
        self.p_day = p_day
        self.p_beginning = p_beginning
        self.p_ending = p_ending
        self.d_day = d_day
        self.md_beginning = md_beginning
        self.md_ending = md_ending

    def run(self):
        try:
            holidays = Holidays(self.ui.organization, self.ui.helper)
            holidays.create_holiday_request(
                self.request_type,
                self.description,
                self.date,
                self.p_day,
                self.p_beginning,
                self.p_ending,
                self.d_day,
                self.md_beginning,
                self.md_ending,
            )
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
