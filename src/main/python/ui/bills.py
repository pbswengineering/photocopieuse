# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime
import os
import traceback
from typing import List, Optional, Callable
import webbrowser

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QComboBox,
    QCommandLinkButton,
    QDateEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QFileDialog,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.bills import Bills
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class BillsUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    tab_widget: QTabWidget
    de_t_due_date: QDateEdit
    de_t_month: QDateEdit
    dsb_t_amount: QDoubleSpinBox
    pte_t_notes: QPlainTextEdit
    clb_t_confluence: QCommandLinkButton
    de_e_due_date: QDateEdit
    le_e_interval: QLineEdit
    dsb_e_amount: QDoubleSpinBox
    pte_e_notes: QPlainTextEdit
    clb_e_confluence: QCommandLinkButton
    de_g_date: QDateEdit
    le_g_interval: QLineEdit
    dsb_g_amount: QDoubleSpinBox
    sb_g_cubic_meters: QSpinBox
    pte_g_notes: QPlainTextEdit
    clb_g_confluence: QCommandLinkButton
    de_w_date: QDateEdit
    le_w_interval: QLineEdit
    dsb_w_amount: QDoubleSpinBox
    cb_w_house: QComboBox
    pte_w_notes: QPlainTextEdit
    clb_w_confluence: QCommandLinkButton
    pb_pdf: QPushButton
    pb_close: QPushButton
    pb_upload: QPushButton
    signal_success = QtCore.pyqtSignal()
    signal_failure = QtCore.pyqtSignal(str)
    pdf_files: List[str]

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
        self.pdf_files = []

    def widget(self) -> QWidget:
        if not self._widget:
            now = datetime.now()
            params = self.helper["parameters"]
            self._widget = uic.loadUi(self.context.get_resource("ui/bills.ui"))
            self.tab_widget = self._widget.findChild(QTabWidget, "tabWidget")
            self.de_t_due_date = self._widget.findChild(QDateEdit, "deTDueDate")
            self.de_t_due_date.setDateTime(now)
            self.de_t_month = self._widget.findChild(QDateEdit, "deTMonth")
            self.de_t_month.setDateTime(now)
            self.dsb_t_amount = self._widget.findChild(QDoubleSpinBox, "dsbTAmount")
            self.pte_t_notes = self._widget.findChild(QPlainTextEdit, "pteTNotes")
            self.clb_t_confluence = self._widget.findChild(
                QCommandLinkButton, "clbTConfluence"
            )
            self.clb_t_confluence.clicked.connect(
                self.clb_x_confluence_clicked("telephone_page")
            )
            self.de_e_due_date = self._widget.findChild(QDateEdit, "deEDueDate")
            self.de_e_due_date.setDateTime(now)
            self.le_e_interval = self._widget.findChild(QLineEdit, "leEInterval")
            self.dsb_e_amount = self._widget.findChild(QDoubleSpinBox, "dsbEAmount")
            self.pte_e_notes = self._widget.findChild(QPlainTextEdit, "pteENotes")
            self.clb_e_confluence = self._widget.findChild(
                QCommandLinkButton, "clbEConfluence"
            )
            self.clb_e_confluence.clicked.connect(
                self.clb_x_confluence_clicked("electricity_page")
            )
            self.de_g_date = self._widget.findChild(QDateEdit, "deGDate")
            self.de_g_date.setDateTime(now)
            self.le_g_interval = self._widget.findChild(QLineEdit, "leGInterval")
            self.dsb_g_amount = self._widget.findChild(QDoubleSpinBox, "dsbGAmount")
            self.sb_g_cubic_meters = self._widget.findChild(QSpinBox, "sbGCubicMeters")
            self.pte_g_notes = self._widget.findChild(QPlainTextEdit, "pteGNotes")
            self.clb_g_confluence = self._widget.findChild(
                QCommandLinkButton, "clbGConfluence"
            )
            self.clb_g_confluence.clicked.connect(
                self.clb_x_confluence_clicked("gas_page")
            )
            self.de_w_date = self._widget.findChild(QDateEdit, "deWDate")
            self.de_w_date.setDateTime(now)
            self.le_w_interval = self._widget.findChild(QLineEdit, "leWInterval")
            self.dsb_w_amount = self._widget.findChild(QDoubleSpinBox, "dsbWAmount")
            self.cb_w_house = self._widget.findChild(QComboBox, "cbWHouse")
            self.cb_w_house.clear()
            self.cb_w_house.addItems(params["houses"].split(","))
            self.pte_w_notes = self._widget.findChild(QPlainTextEdit, "pteWNotes")
            self.clb_w_confluence = self._widget.findChild(
                QCommandLinkButton, "clbWConfluence"
            )
            self.clb_w_confluence.clicked.connect(
                self.clb_x_confluence_clicked("water_page")
            )
            self.pb_pdf = self._widget.findChild(QPushButton, "pbPDF")
            self.pb_pdf.clicked.connect(self.pb_pdf_clicked)
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_upload = self._widget.findChild(QPushButton, "pbUpload")
            self.pb_upload.clicked.connect(self.pb_upload_clicked)
            self.signal_failure.connect(self.failure)
            self.signal_success.connect(self.success)
        return self._widget

    def pb_pdf_clicked(self):
        files = QFileDialog.getOpenFileNames(
            self._widget, "Open PDF files", os.path.expanduser("~"), "PDF files (*.pdf)"
        )[0]
        if files:
            self.pdf_files = files
            self.pb_pdf.setText(
                f"{len(files)} file{len(files) > 1 and 's' or ''} selected"
            )

    def active(self, state: bool):
        self.tab_widget.setEnabled(state)
        self.de_t_due_date.setEnabled(state)
        self.de_t_month.setEnabled(state)
        self.dsb_t_amount.setEnabled(state)
        self.pte_t_notes.setEnabled(state)
        self.de_e_due_date.setEnabled(state)
        self.le_e_interval.setEnabled(state)
        self.dsb_e_amount.setEnabled(state)
        self.pte_e_notes.setEnabled(state)
        self.de_g_date.setEnabled(state)
        self.le_g_interval.setEnabled(state)
        self.dsb_g_amount.setEnabled(state)
        self.sb_g_cubic_meters.setEnabled(state)
        self.pte_g_notes.setEnabled(state)
        self.de_w_date.setEnabled(state)
        self.le_w_interval.setEnabled(state)
        self.dsb_w_amount.setEnabled(state)
        self.cb_w_house.setEnabled(state)
        self.pte_w_notes.setEnabled(state)
        self.pb_pdf.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.pb_upload.setEnabled(state)

    def clb_x_confluence_clicked(self, page_parameter: str) -> Callable:
        def clicked():
            params = self.helper["parameters"]
            webbrowser.open(params[page_parameter].replace("[house]", self.cb_w_house.currentText()))
        return clicked

    def pb_upload_clicked(self):
        request_type = self.tab_widget.currentIndex()
        if len(self.pdf_files) == 0:
            self.message_error("Please select at least one PDF file")
            return
        # 0 - Telephone
        t_due_date = self.de_t_due_date.dateTime().toPyDateTime()
        t_month = self.de_t_month.dateTime().toPyDateTime()
        t_amount = self.dsb_t_amount.value()
        t_notes = self.pte_t_notes.toPlainText()
        # 1 - Electricity
        e_due_date = self.de_e_due_date.dateTime().toPyDateTime()
        e_interval = self.le_e_interval.text()
        e_amount = self.dsb_e_amount.value()
        e_notes = self.pte_e_notes.toPlainText()
        # 2 - Gas
        g_date = self.de_g_date.dateTime().toPyDateTime()
        g_interval = self.le_g_interval.text()
        g_amount = self.dsb_g_amount.value()
        g_cubic_meters = self.sb_g_cubic_meters.value()
        g_notes = self.pte_g_notes.toPlainText()
        # 3 - Water
        w_date = self.de_w_date.dateTime().toPyDateTime()
        w_interval = self.le_w_interval.text()
        w_amount = self.dsb_w_amount.value()
        w_house = self.cb_w_house.currentText()
        w_notes = self.pte_w_notes.toPlainText()
        self.active(False)
        self.context.show_status("Updating the wiki page...")
        BillsTask(
            self,
            request_type,
            t_due_date,
            t_month,
            t_amount,
            t_notes,
            e_due_date,
            e_interval,
            e_amount,
            e_notes,
            g_date,
            g_interval,
            g_amount,
            g_cubic_meters,
            g_notes,
            w_date,
            w_interval,
            w_amount,
            w_house,
            w_notes,
            self.pdf_files,
        ).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info("The wiki page has been updated successfully")


class BillsTask(BaseTask):
    ui: BillsUI
    request_type: int
    t_due_date: datetime
    t_month: datetime
    t_amount: float
    t_notes: str
    e_due_date: datetime
    e_interval: str
    e_amount: float
    e_notes: str
    g_date: datetime
    g_interval: str
    g_amount: float
    g_cubic_meters: int
    g_notes: str
    w_date: datetime
    w_interval: str
    w_amount: float
    w_house: str
    w_notes: str
    pdf_files: List[str]

    def __init__(
        self,
        ui: BillsUI,
        request_type: int,
        t_due_date: datetime,
        t_month: datetime,
        t_amount: float,
        t_notes: str,
        e_due_date: datetime,
        e_interval: str,
        e_amount: float,
        e_notes: str,
        g_date: datetime,
        g_interval: str,
        g_amount: float,
        g_cubic_meters: int,
        g_notes: str,
        w_date: datetime,
        w_interval: str,
        w_amount: float,
        w_house: str,
        w_notes: str,
        pdf_files: List[str],
    ):
        super().__init__()
        self.ui = ui
        self.request_type = request_type
        self.t_due_date = t_due_date
        self.t_month = t_month
        self.t_amount = t_amount
        self.t_notes = t_notes
        self.e_due_date = e_due_date
        self.e_interval = e_interval
        self.e_amount = e_amount
        self.e_notes = e_notes
        self.g_date = g_date
        self.g_interval = g_interval
        self.g_amount = g_amount
        self.g_cubic_meters = g_cubic_meters
        self.g_notes = g_notes
        self.w_date = w_date
        self.w_interval = w_interval
        self.w_amount = w_amount
        self.w_house = w_house
        self.w_notes = w_notes
        self.pdf_files = pdf_files

    def run(self):
        try:
            bills = Bills(self.ui.organization, self.ui.helper)
            if self.request_type == 0:  # 0 - Telephone
                bills.upload_telephone(
                    self.t_due_date,
                    self.t_month,
                    self.t_amount,
                    self.t_notes,
                    self.pdf_files,
                )
            elif self.request_type == 1:  # 1 - Electricity
                bills.upload_electricity(
                    self.e_due_date,
                    self.e_interval,
                    self.e_amount,
                    self.e_notes,
                    self.pdf_files,
                )
            elif self.request_type == 2:  # 2 - Gas
                bills.upload_gas(
                    self.g_date,
                    self.g_interval,
                    self.g_amount,
                    self.g_cubic_meters,
                    self.g_notes,
                    self.pdf_files,
                )
            elif self.request_type == 3:  # 3 - Water
                bills.upload_water(
                    self.w_date,
                    self.w_interval,
                    self.w_amount,
                    self.w_house,
                    self.w_notes,
                    self.pdf_files,
                )
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
