# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import threading

import utils


class BaseTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        utils.set_default_locale()
