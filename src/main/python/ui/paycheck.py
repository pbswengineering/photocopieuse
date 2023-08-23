# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import logging
from datetime import datetime
from math import floor
import os
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QLineEdit,
    QPushButton,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.paycheck import Paycheck
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class PaycheckUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    _widget: Optional[QWidget]
    de_day: QDateEdit
    dsb_gross: QDoubleSpinBox
    dsb_net: QDoubleSpinBox
    cb_type: QComboBox
    le_notes: QLineEdit
    pb_pdf: QPushButton
    pb_close: QPushButton
    pb_upload: QPushButton
    signal_success = QtCore.pyqtSignal()
    signal_failure = QtCore.pyqtSignal(str)
    pdf_file: Optional[str]

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
        self.pdf_file = None

    def widget(self) -> QWidget:
        if not self._widget:
            self._widget = uic.loadUi(self.context.get_resource("ui/paycheck.ui"))
            self.de_day = self._widget.findChild(QDateEdit, "deDay")
            self.de_day.setDateTime(datetime.now())
            self.dsb_gross = self._widget.findChild(QDoubleSpinBox, "dsbGross")
            self.dsb_net = self._widget.findChild(QDoubleSpinBox, "dsbNet")
            self.le_notes = self._widget.findChild(QLineEdit, "leNotes")
            self.pb_pdf = self._widget.findChild(QPushButton, "pbPdf")
            self.pb_pdf.clicked.connect(self.pb_pdf_clicked)
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_upload = self._widget.findChild(QPushButton, "pbUpload")
            self.pb_upload.clicked.connect(self.pb_upload_clicked)
            self.signal_failure.connect(self.failure)
            self.signal_success.connect(self.success)
        return self._widget

    def active(self, state: bool):
        self.de_day.setEnabled(state)
        self.dsb_gross.setEnabled(state)
        self.dsb_net.setEnabled(state)
        self.le_notes.setEnabled(state)
        self.pb_pdf.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_upload.setEnabled(state)

    def pb_pdf_clicked(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("PDF files (*.pdf)")
        if dlg.exec_():
            files = dlg.selectedFiles()
            if files:
                self.pdf_file = files[0]
                self.pb_pdf.setText(os.path.basename(self.pdf_file))

    def pb_upload_clicked(self):
        day = self.de_day.dateTime().toPyDateTime()
        gross = self.dsb_gross.value()
        net = self.dsb_net.value()
        notes = self.le_notes.text()
        if not self.pdf_file:
            self.message_error("Please select the paycheck PDF file")
            return
        self.active(False)
        self.context.show_status("Uploading the paycheck and updating the wiki page...")
        PaycheckTask(
            self,
            day,
            gross,
            net,
            self.pdf_file,
            notes
        ).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info("The wiki page has been updated correctly")


class PaycheckTask(BaseTask):
    ui: PaycheckUI
    day: datetime
    gross: float
    net: float
    pdf: str
    notes: str

    def __init__(
        self,
        ui: PaycheckUI,
        day: datetime,
        gross: float,
        net: float,
        pdf: str,
        notes: str
    ):
        super().__init__()
        self.ui = ui
        self.day = day
        self.gross = gross
        self.net = net
        self.pdf = pdf
        self.notes = notes

    def run(self):
        try:
            paycheck = Paycheck(self.ui.organization, self.ui.helper)
            paycheck.upload_paycheck(
                self.day,
                self.gross,
                self.net,
                self.pdf,
                self.notes
            )
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
