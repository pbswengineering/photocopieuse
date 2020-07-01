# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from typing import List, Optional

from server.badgebox import BadgeBox
from server.caldav import CalDAV
from server.confluence import Confluence
from server.jira import Jira
from server.smtp import SMTP


class Organization:
    """
    Generic organization (a company, an nonprofit organization,
    an individual etc.)
    """

    name: str
    _jira: Optional[Jira]
    _jira_users: Optional[List[str]]
    _jira_timetracker_url: Optional[str]
    _confluence: Optional[Confluence]
    _calendar: Optional[CalDAV]
    _badgebox: Optional[BadgeBox]
    _smtp: Optional[SMTP]

    def __init__(self, name):
        self.name = name
        self._jira = None
        self._confluence = None
        self._calendar = None
        self._badgebox = None
        self._excel_reports = None
        self._smtp = None

    def set_jira(self, jira: Optional[Jira]):
        self._jira = jira

    def jira(self) -> Jira:
        if not self._jira:
            raise Exception(f"{self.name} Jira is not configured")
        else:
            return self._jira

    def set_confluence(self, confluence: Optional[Confluence]):
        self._confluence = confluence

    def confluence(self) -> Confluence:
        if not self._confluence:
            raise Exception(f"{self.name} Confluence is not configured")
        else:
            return self._confluence

    def set_calendar(self, calendar: Optional[CalDAV]):
        self._calendar = calendar

    def calendar(self) -> CalDAV:
        if not self._calendar:
            raise Exception(f"{self.name} calendar is not configured")
        else:
            return self._calendar

    def set_badgebox(self, badgebox: Optional[BadgeBox]):
        self._badgebox = badgebox

    def badgebox(self) -> BadgeBox:
        if not self._badgebox:
            raise Exception(f"{self.name} BadgeBox is not configured")
        else:
            return self._badgebox

    def set_smtp(self, smtp: Optional[SMTP]):
        self._smtp = smtp

    def smtp(self) -> SMTP:
        if not self._smtp:
            raise Exception(f"{self.name} SMTP is not configured")
        else:
            return self._smtp
