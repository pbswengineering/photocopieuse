# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import logging
from typing import Callable, Dict, List

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QGroupBox,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QWidget,
    QAction,
    QDialog,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QApplication,
)

from config import Config, HelperType
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.cryptogram import CryptoGramUI  # noqa: F401
from ui.lifelong_learning import LifelongLearningUI  # noqa: F401
from ui.letsencrypt import LetsEncryptUI  # noqa: F401
from ui.bills import BillsUI  # noqa: F401
from ui.clockings import ClockingsUI  # noqa: F401
from ui.holidays import HolidayUI  # noqa: F401
from ui.paycheck import PaycheckUI  # noqa: F401
from ui.pregnancy import PregnancyUI  # noqa: F401
from ui.phabricator_files import PhabricatorFilesUI  # noqa: F401
from ui.travels import TravelsUI  # noqa: F401


class AppContext(AbstractContext):
    qapp: QApplication
    config: Config
    window: QMainWindow
    central_widget: QWidget
    status_bar: QStatusBar
    groupboxes: List[QGroupBox]
    helper_uis: Dict[str, AbstractUI]
    action_about: QAction
    action_exit: QAction

    def __init__(self, qapp: QApplication):
        super(AppContext, self).__init__()
        self.qapp = qapp
        self.helper_mode = False
        self.window = uic.loadUi(self.get_resource("ui/main.ui"))
        self.central_widget = self.window.findChild(QWidget, "centralwidget")
        self.config = Config(self.qapp)
        self.groupboxes = []
        self.helper_uis = {}
        for org in self.config.organizations():
            gb = QGroupBox(org.name)
            self.central_widget.layout().addWidget(gb)
            vbox = QVBoxLayout()
            for helper in self.config.helpers():
                if helper.get("display_organization", org.name) != org.name:
                    continue
                elif helper["organization"] != org.name:
                    continue
                elif helper.get("hidden"):
                    continue
                pb = QPushButton(helper["name"])
                pb.setStyleSheet("QPushButton {font-weight: bold; height: 40px}")
                pb.clicked.connect(self.helper_clicked(helper))
                vbox.addWidget(pb)
            vbox.addItem(
                QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            )
            gb.setLayout(vbox)
            self.groupboxes.append(gb)
        self.status_bar = self.window.findChild(QStatusBar, "statusbar")
        self.action_about = self.window.findChild(QAction, "actionAbout")
        self.action_about.triggered.connect(self.action_about_triggered)
        self.action_exit = self.window.findChild(QAction, "actionExit")
        self.action_exit.triggered.connect(self.action_exit_triggered)

    def run(self):
        self.window.show()
        return self.app.exec_()

    def helper_ui(self, helper: HelperType) -> AbstractUI:
        ui_name = str(helper["ui"])
        if ui_name not in self.helper_uis:
            helper_org = self.config.organization(helper["organization"])
            helper_ui = globals()[ui_name](self, helper_org, helper, self.app)
            self.helper_uis[ui_name] = helper_ui
        return self.helper_uis[ui_name]

    def helper_clicked(self, helper: HelperType) -> Callable:
        ui = self.helper_ui(helper)

        def clicked():
            logging.debug(helper["name"])
            self.open_widget(ui.widget())
            if "resize" in helper:
                self.resize(helper["resize"][0], helper["resize"][1])

        return clicked

    def action_about_triggered(self):
        about_dialog = uic.loadUi(self.get_resource("ui/about.ui"))  # type: QDialog
        pb_close = about_dialog.findChild(QPushButton, "pbClose")  # type: QPushButton
        pb_close.clicked.connect(about_dialog.close)
        about_dialog.exec_()

    def action_exit_triggered(self):
        self.window.close()

    def resize(self, w: int, h: int):
        if self.window.isMaximized():
            self.window.showNormal()
        self.window.resize(w, h)

    def show_status(self, message: str):
        self.status_bar.showMessage(message)

    def clear_status(self):
        self.status_bar.clearMessage()

    def open_widget(self, widget: QWidget):
        for gb in self.groupboxes:
            gb.hide()
        self.central_widget.layout().addWidget(widget)
        widget.show()

    def close_widget(self, widget: QWidget):
        self.central_widget.layout().removeWidget(widget)
        widget.hide()
        for gb in self.groupboxes:
            gb.show()
        self.resize(477, 291)
