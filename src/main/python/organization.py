# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from typing import List, Optional

from server.caldav import CalDAV
from server.smtp import SMTP
from server.ftp import FTP


class Organization:
    """
    Generic organization (a company, an nonprofit organization,
    an individual etc.)
    """

    name: str
    _jira_users: Optional[List[str]]
    _jira_timetracker_url: Optional[str]
    _calendar: Optional[CalDAV]
    _smtp: Optional[SMTP]
    _ftp: Optional[FTP]

    def __init__(self, name):
        self.name = name
        self._calendar = None
        self._excel_reports = None
        self._smtp = None
        self._ftp = None

    def set_calendar(self, calendar: Optional[CalDAV]):
        self._calendar = calendar

    def calendar(self) -> CalDAV:
        if not self._calendar:
            raise Exception(f"{self.name} calendar is not configured")
        else:
            return self._calendar

    def set_smtp(self, smtp: Optional[SMTP]):
        self._smtp = smtp

    def smtp(self) -> SMTP:
        if not self._smtp:
            raise Exception(f"{self.name} SMTP is not configured")
        else:
            return self._smtp

    def set_ftp(self, ftp: Optional[FTP]):
        self._ftp = ftp

    def ftp(self) -> FTP:
        if not self._ftp:
            raise Exception(f"{self.name} FTP is not configured")
        else:
            return self._ftp
