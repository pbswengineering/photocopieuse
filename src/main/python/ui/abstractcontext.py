# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from abc import ABC, abstractmethod

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QWidget


class AbstractContext(ABC, ApplicationContext):
    helper_mode: bool

    @abstractmethod
    def open_widget(self, widget: QWidget):
        pass

    @abstractmethod
    def close_widget(self, widget: QWidget):
        pass

    @abstractmethod
    def show_status(self, message: str):
        pass

    @abstractmethod
    def clear_status(self):
        pass
