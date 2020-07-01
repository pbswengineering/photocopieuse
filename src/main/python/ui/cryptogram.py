# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import month_name
import logging
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.cryptogram import CryptoGram
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class CryptoGramUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    cb_month: QComboBox
    le_year: QLineEdit
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
            self._widget = uic.loadUi(self.context.get_resource("ui/cryptogram.ui"))
            self.cb_month = self._widget.findChild(QComboBox, "cbMonth")
            month_list = [month_name[i] for i in range(1, 13)]
            self.cb_month.addItems(month_list)
            self.le_year = self._widget.findChild(QLineEdit, "leYear")
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_schedule = self._widget.findChild(QPushButton, "pbSchedule")
            self.pb_schedule.clicked.connect(self.pb_schedule_clicked)
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
        return self._widget

    def active(self, state):
        self.cb_month.setEnabled(state)
        self.le_year.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_schedule.setEnabled(state)

    def pb_schedule_clicked(self):
        try:
            month = self.cb_month.currentIndex() + 1
        except Exception as e:
            logging.error(e)
            self.message_error("The month is incorrect")
            return
        try:
            year = int(self.le_year.text())
        except Exception as e:
            logging.error(e)
            self.message_error("The year is incorrect")
            return
        self.active(False)
        self.context.show_status("Creating Jira ticket and calendar event...")
        CryptoGramTask(self, month, year).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info(
            "The Jira ticket and the calendar event have been created correctly."
        )


class CryptoGramTask(BaseTask):
    ui: CryptoGramUI
    month: int
    year: int

    def __init__(self, ui: CryptoGramUI, month: int, year: int):
        super().__init__()
        self.ui = ui
        self.month = month
        self.year = year

    def run(self):
        try:
            cryptogram = CryptoGram(self.ui.organization, self.ui.helper)
            cryptogram.schedule(self.month, self.year)
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
