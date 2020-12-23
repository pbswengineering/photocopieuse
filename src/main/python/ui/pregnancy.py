# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import os
from typing import Callable, Optional
import webbrowser

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget,
    QApplication,
    QLabel,
    QCommandLinkButton,
)

from config import HelperType
from organization import Organization
from service.pregnancy import Pregnancy
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI


class PregnancyUI(AbstractUI):
    context: AbstractContext
    organization: Organization
    helper: HelperType
    _widget: Optional[QWidget]
    lb_lmp: QLabel
    lb_edd: QLabel
    lb_ga: QLabel
    lb_week: QLabel
    lb_trimester: QLabel
    clb_confluence: QCommandLinkButton
    clb_extra_link: QCommandLinkButton
    pb_close: QPushButton

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
            self._widget = uic.loadUi(self.context.get_resource("ui/pregnancy.ui"))
            self.lb_lmp = self._widget.findChild(QLabel, "lbLMP")
            self.lb_edd = self._widget.findChild(QLabel, "lbEDD")
            self.lb_ga = self._widget.findChild(QLabel, "lbGA")
            self.lb_week = self._widget.findChild(QLabel, "lbWeek")
            self.lb_trimester = self._widget.findChild(QLabel, "lbTrimester")
            self.clb_confluence = self._widget.findChild(QCommandLinkButton, "clbConfluence")
            self.clb_confluence.clicked.connect(self.clb_confluence_clicked("telephone_page"))
            self.clb_extra_link = self._widget.findChild(QCommandLinkButton, "clbExtraLink")
            params = self.helper["parameters"]
            if "extra_link_url" in params and "extra_link_text" in params:
                self.clb_extra_link.clicked.connect(self.clb_extra_link_clicked)
                self.clb_extra_link.setText(params["extra_link_text"])
            else:
                self.clb_extra_link.setVisible(False)
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            pregnancy = Pregnancy(self.organization, self.helper)
            DATE_FORMAT = "%Y-%m-%d"
            self.lb_lmp.setText(pregnancy.lmp.strftime(DATE_FORMAT))
            self.lb_edd.setText(pregnancy.edd.strftime(DATE_FORMAT))
            self.lb_ga.setText(pregnancy.ga)
            self.lb_week.setText(str(pregnancy.week))
            self.lb_trimester.setText(str(pregnancy.trimester))
        return self._widget

    def active(self, state):
        self.lb_lmp.setEnabled(state)
        self.lb_edd.setEnabled(state)
        self.lb_ga.setEnabled(state)
        self.lb_week.setEnabled(state)
        self.lb_trimester.setEnabled(state)
        self.pb_close.setEnabled(state)

    def clb_confluence_clicked(self, page_parameter: str) -> Callable:
        def clicked():
            params = self.helper["parameters"]
            space = params["confluence_space"]
            page = params["confluence_page"]
            webbrowser.open(
                os.path.join(
                    self.organization.confluence().url,
                    f"display/{space}/{page}",
                )
            )
        return clicked
    
    def clb_extra_link_clicked(self):
        webbrowser.open(self.helper["parameters"]["extra_link_url"])