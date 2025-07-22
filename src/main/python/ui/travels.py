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
from service.travels import Travels
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class TravelsUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    cb_month: QComboBox
    le_year: QLineEdit
    le_destination: QLineEdit
    le_description: QLineEdit
    pb_close: QPushButton
    pb_create: QPushButton
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
            self._widget = uic.loadUi(self.context.get_resource("ui/travels.ui"))
            self.cb_month = self._widget.findChild(QComboBox, "cbMonth")
            month_list = [month_name[i] for i in range(1, 13)]
            self.cb_month.addItems(month_list)
            self.le_year = self._widget.findChild(QLineEdit, "leYear")
            self.le_destination = self._widget.findChild(QLineEdit, "leDestination")
            self.le_description = self._widget.findChild(QLineEdit, "leDescription")
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_create = self._widget.findChild(QPushButton, "pbCreate")
            self.pb_create.clicked.connect(self.pb_create_clicked)
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
        return self._widget

    def active(self, state):
        self.cb_month.setEnabled(state)
        self.le_year.setEnabled(state)
        self.le_destination.setEnabled(state)
        self.le_description.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_create.setEnabled(state)

    def pb_create_clicked(self):
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
        destination = self.le_destination.text()
        if not destination:
            logging.error("Missing destination")
            self.message_error("The destination is missing")
            return
        description = self.le_description.text()
        if not description:
            logging.error("Missing description")
            self.message_error("The description is missing")
            return
        self.active(False)
        self.context.show_status("Creating wiki page and media directory...")
        TravelsTask(self, month, year, destination, description).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info(
            "The wiki page and media directory have been created correctly."
        )


class TravelsTask(BaseTask):
    ui: TravelsUI
    month: int
    year: int
    destination: str
    description: str

    def __init__(self, ui: TravelsUI, month: int, year: int, destination: str, description: str):
        super().__init__()
        self.ui = ui
        self.month = month
        self.year = year
        self.destination = destination
        self.description = description

    def run(self):
        try:
            travels = Travels(self.ui.organization, self.ui.helper)
            travels.create(self.month, self.year, self.destination, self.description)
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
