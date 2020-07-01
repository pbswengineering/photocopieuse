# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import monthrange
from datetime import datetime, timedelta
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from server.badgebox import Records
from service.clockings import Clockings
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class ClockingsUI(AbstractUI):
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    cb_month: QComboBox
    pb_close: QPushButton
    table: QTableWidget

    signal_success = QtCore.pyqtSignal(datetime, Records)
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
            self._widget = uic.loadUi(self.context.get_resource("ui/clockings.ui"))
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            # List of months
            self.cb_month = self._widget.findChild(QComboBox, "cbMonth")
            day = datetime.now()  # type: datetime
            month_list = []
            for i in range(20):
                month_list.append(day.strftime("%Y-%m"))
                day = day.replace(day=1) - timedelta(days=1)
            self.cb_month.addItems(month_list)
            self.cb_month.currentIndexChanged.connect(self.cb_month_changed)
            # Table of results
            self.table = self._widget.findChild(QTableWidget, "table")
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
        self.resize_table()
        self.cb_month_changed()
        return self._widget

    def active(self, state):
        self.cb_month.setEnabled(state)
        self.pb_close.setEnabled(state)
        self.table.setEnabled(state)

    def cb_month_changed(self):
        date_str = self.cb_month.currentText()
        self.active(False)
        date = datetime.strptime(date_str, "%Y-%m")
        self.table.setRowCount(0)
        self.context.show_status("Download in progress...")
        ClockingsTask(self, date).start()

    def resize_table(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self, date: datetime, records: Records):
        self.active(True)
        _, days_in_month = monthrange(date.year, date.month)
        self.table.setRowCount(days_in_month)
        today = datetime.now().strftime("%Y-%m-%d")
        today_row = None
        for row, (d, recs) in enumerate(records.records.items()):
            if today == d:
                today_row = row
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B")),
            )
            widget = QWidget()
            widget_text = QLabel("<br>".join(str(r) for r in recs))
            widget_layout = QHBoxLayout()
            widget_layout.addWidget(widget_text)
            widget_layout.setSizeConstraint(QLayout.SetFixedSize)
            widget.setLayout(widget_layout)
            self.table.setCellWidget(row, 1, widget)
        self.resize_table()
        self.table.resizeRowsToContents()
        self.context.clear_status()
        if today_row is not None:
            self.table.selectRow(today_row)


class ClockingsTask(BaseTask):
    ui: ClockingsUI
    date: datetime

    def __init__(self, ui: ClockingsUI, date: datetime):
        super().__init__()
        self.ui = ui
        self.date = date

    def run(self):
        try:
            clockings = Clockings(self.ui.organization)
            records = clockings.get_clockings(self.date)
            self.ui.signal_success.emit(self.date, records)
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
