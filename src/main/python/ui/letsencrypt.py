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
from PyQt5.QtWidgets import (
    QDateEdit,
    QPushButton,
    QTimeEdit,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.lets_encrypt import LetsEncrypt
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class LetsEncryptUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    _widget: Optional[QWidget]
    de_day: QDateEdit
    te_time: QTimeEdit
    pb_close: QPushButton
    pb_schedule: QPushButton
    message = QtCore.pyqtSignal(str)
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
            self._widget = uic.loadUi(self.context.get_resource("ui/lets_encrypt.ui"))
            now = datetime.now()
            self.de_day = self._widget.findChild(QDateEdit, "deDay")
            self.de_day.setDateTime(now)
            self.te_time = self._widget.findChild(QTimeEdit, "teTime")
            self.te_time.setDateTime(now)
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_schedule = self._widget.findChild(QPushButton, "pbSchedule")
            self.pb_schedule.clicked.connect(self.pb_schedule_clicked)
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
        return self._widget

    def active(self, state):
        self.de_day.setEnabled(state)
        self.te_time.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_schedule.setEnabled(state)

    def pb_schedule_clicked(self):
        try:
            day = self.de_day.date().toPyDate().strftime("%Y-%m-%d")
        except Exception as e:
            logging.error(e)
            self.message_error("The day is incorrect")
            return
        try:
            hour = self.te_time.time().toString("HH.mm")
        except Exception as e:
            logging.error(e)
            self.message_error("The hour is incorrect")
            return
        self.active(False)
        self.context.show_status("Creating Maniphest ticket and calendar event...")
        date = datetime.strptime(f"{day} {hour}", "%Y-%m-%d %H.%M")
        LetsEncryptTask(self, date).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info(
            "The Maniphest ticket and the calendar event have been created correctly."
        )


class LetsEncryptTask(BaseTask):
    ui: LetsEncryptUI
    date: datetime

    def __init__(self, ui: LetsEncryptUI, date: datetime):
        super().__init__()
        self.ui = ui
        self.date = date

    def run(self):
        try:
            lets_encrypt = LetsEncrypt(self.ui.organization, self.ui.helper)
            lets_encrypt.schedule(self.date)
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
