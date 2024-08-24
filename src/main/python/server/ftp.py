# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import logging
import os
from typing import List, Optional

import ftputil


class FTP:
    """
    FTP server.
    """

    host: str
    port: int
    user: str
    password: str
    host: ftputil.FTPHost

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.host = ftputil.FTPHost(host, user, password)
