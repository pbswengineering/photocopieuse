# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime, timedelta
import logging
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.Qt import QTime
from PyQt5.QtWidgets import (
    QDateEdit,
    QLineEdit,
    QPushButton,
    QTimeEdit,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.lifelong_learning import LifelongLearning
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class LifelongLearningUI(AbstractUI):

    context: AbstractContext
    organization: Organization
    _widget: Optional[QWidget]
    le_code: QLineEdit
    le_title: QLineEdit
    le_location: QLineEdit
    de_day: QDateEdit
    te_beginning: QTimeEdit
    te_ending: QTimeEdit
    le_credits: QLineEdit
    le_notes: QLineEdit
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
            self._widget = uic.loadUi(
                self.context.get_resource("ui/lifelong_learning.ui")
            )
            self.le_code = self._widget.findChild(QLineEdit, "leCode")
            self.le_title = self._widget.findChild(QLineEdit, "leTitle")
            self.le_location = self._widget.findChild(QLineEdit, "leLocation")
            self.de_day = self._widget.findChild(QDateEdit, "deDay")
            now = datetime.now()
            self.de_day.setDate(now)
            self.te_beginning = self._widget.findChild(QTimeEdit, "teBeginning")
            self.te_beginning.setTime(QTime(now.hour, now.minute))
            self.te_ending = self._widget.findChild(QTimeEdit, "teEnding")
            now += timedelta(seconds=3600)
            self.te_ending.setTime(QTime(now.hour, now.minute))
            self.le_credits = self._widget.findChild(QLineEdit, "leCredits")
            self.le_notes = self._widget.findChild(QLineEdit, "leNotes")
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_schedule = self._widget.findChild(QPushButton, "pbSchedule")
            self.pb_schedule.clicked.connect(self.pb_schedule_clicked)
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
        return self._widget

    def active(self, state):
        self.le_code.setEnabled(state)
        self.le_title.setEnabled(state)
        self.le_location.setEnabled(state)
        self.de_day.setEnabled(state)
        self.te_beginning.setEnabled(state)
        self.te_ending.setEnabled(state)
        self.le_credits.setEnabled(state)
        self.le_notes.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_schedule.setEnabled(state)

    def pb_schedule_clicked(self):
        code = self.le_code.text().strip()
        if not code:
            self.message_error("The code is incorrect")
            return
        title = self.le_title.text().strip()
        if not title:
            self.message_error("The title is incorrect")
            return
        location = self.le_location.text().strip()
        if not location:
            self.message_error("The location is incorrect")
            return
        try:
            day_str = self.de_day.date().toString("yyyy-MM-dd")
        except Exception as e:
            logging.error(e)
            self.message_error("The day is incorrect")
            return
        try:
            beginning_str = self.te_beginning.time().toString("HH.mm")
            beginning = datetime.strptime(
                f"{day_str} {beginning_str}", "%Y-%m-%d %H.%M"
            )
        except Exception as e:
            logging.error(e)
            self.message_error("The beginning time is incorrect")
            return
        try:
            ending_str = self.te_ending.time().toString("HH.mm")
            ending = datetime.strptime(f"{day_str} {ending_str}", "%Y-%m-%d %H.%M")
        except Exception as e:
            logging.error(e)
            self.message_error("The ending time is incorrect")
            return
        try:
            credits = int(self.le_credits.text().strip())
        except Exception as e:
            logging.error(e)
            self.message_error("The credits are incorrect")
            return
        notes = self.le_notes.text().strip()
        self.active(False)
        self.context.show_status(
            "Creating Jira ticket, calendar event and Confluence page..."
        )
        LifelongLearningTask(
            self, code, title, location, beginning, ending, credits, notes
        ).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info(
            "The Jira ticket, the calendar event and the Confluence page have been created correctly."
        )


class LifelongLearningTask(BaseTask):
    ui: LifelongLearningUI
    code: str
    title: str
    location: str
    beginning: datetime
    ending: datetime
    credits: int
    notes: str

    def __init__(
        self,
        ui: LifelongLearningUI,
        code: str,
        title: str,
        location: str,
        beginning: datetime,
        ending: datetime,
        credits: int,
        notes: str,
    ):
        super().__init__()
        self.ui = ui
        self.code = code
        self.title = title
        self.location = location
        self.beginning = beginning
        self.ending = ending
        self.credits = credits
        self.notes = notes

    def run(self):
        try:
            lifelong_learning = LifelongLearning(self.ui.organization, self.ui.helper)
            lifelong_learning.schedule(
                self.code,
                self.title,
                self.location,
                self.beginning,
                self.ending,
                self.credits,
                self.notes,
            )
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
