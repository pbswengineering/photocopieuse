# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import month_name
import logging
import os
import traceback
from typing import Optional

from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import (
    QLineEdit,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask


class PhabricatorFilesUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    pb_file: QPushButton
    le_name: QLineEdit
    pb_upload: QPushButton
    pbar_upload: QProgressBar
    le_file_id: QLineEdit
    pb_close: QPushButton
    message = QtCore.pyqtSignal(str)
    signal_progress = QtCore.pyqtSignal(int, int)
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
        self.file = None

    def widget(self) -> QWidget:
        if not self._widget:
            self._widget = uic.loadUi(self.context.get_resource("ui/phabricator_files.ui"))
            self.pb_file = self._widget.findChild(QPushButton, "pbFile")
            self.pb_file.clicked.connect(self.pb_file_clicked)
            self.le_name = self._widget.findChild(QLineEdit, "leName")
            self.pbar_upload = self._widget.findChild(QProgressBar, "pbarUpload")
            self.le_file_id = self._widget.findChild(QLineEdit, "leFileId")
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_upload = self._widget.findChild(QPushButton, "pbUpload")
            self.pb_upload.clicked.connect(self.pb_upload_clicked)
            self.signal_success.connect(self.success)
            self.signal_failure.connect(self.failure)
            self.signal_progress.connect(self.show_progress)
        return self._widget

    def active(self, state):
        self.pb_file.setEnabled(state)
        self.le_name.setEnabled(state)
        self.pbar_upload.setEnabled(state)
        self.le_name.setEnabled(state)
        self.pb_upload.setEnabled(state)
        self.pb_close.setEnabled(state)
    
    def pb_file_clicked(self):
        file = QFileDialog.getOpenFileName(
            self._widget, "Open file", os.path.expanduser("~"), "Any file (*.*)"
        )[0]
        if file:
            self.file = file
            base_name = os.path.basename(file)
            self.pb_file.setText(base_name)
            self.le_name.setText(os.path.basename(file))

    def pb_upload_clicked(self):
        if not self.file:
            self.message_error("Please select a file")
            return
        try:
            name = self.le_name.text()
        except Exception as e:
            logging.error(e)
            self.message_error("The name is incorrect")
            return
        self.active(False)
        self.context.show_status("FIle upload in progress...")
        PhabricatorFilesTask(self, name).start()

    def failure(self, message: str):
        self.message_error(message)
        self.context.clear_status()
        self.active(True)

    def success(self):
        self.context.clear_status()
        self.active(True)
        self.message_info("The file was uploaded correctly")
    
    def show_progress(self, value: int, max_value: int):
        self.pbar_upload.setValue(value)
        self.pbar_upload.setMaximum(max_value)


class PhabricatorFilesTask(BaseTask):
    ui: PhabricatorFilesUI
    name: str

    def __init__(self, ui: PhabricatorFilesUI, name: str):
        super().__init__()
        self.ui = ui
        self.name = name

    def run(self):
        try:
            phab = self.ui.organization.phabricator()
            phid = phab.upload_file(self.ui.file, self.name, self.ui.signal_progress)
            file = phab.get_file_by_phid(phid)
            self.ui.le_file_id.setText(f"F{file['id']}")
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
