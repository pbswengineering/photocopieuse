# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from abc import abstractmethod

from PyQt5 import QtCore
from PyQt5.Qt import QMessageBox
from PyQt5.QtWidgets import QApplication, QWidget

from ui.abstractcontext import AbstractContext


class AbstractUI(QtCore.QObject):
    context: AbstractContext

    def __init__(self, app: QApplication, context: AbstractContext):
        QtCore.QObject.__init__(self)
        self.app = app
        self.context = context

    def pb_close_clicked(self):
        if self.context.helper_mode:
            self.app.quit()
        else:
            self.context.close_widget(self.widget())

    def message_info(self, message: str):
        QMessageBox.information(self.widget(), "Photocopieuse", message)

    def message_error(self, message: str):
        QMessageBox.critical(self.widget(), "Photocopieuse", message)

    def message_yes_no(self, question: str):
        return (
            QMessageBox.question(
                self.widget(),
                "Photocopieuse",
                question,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    @abstractmethod
    def widget(self) -> QWidget:
        pass
