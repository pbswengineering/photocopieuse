# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import monthrange
from datetime import datetime

from organization import Organization
from server.badgebox import Records


class Clockings:
    org: Organization

    def __init__(self, org: Organization):
        self.org = org

    def get_clockings(self, date: datetime) -> Records:
        badgebox = self.org.badgebox()
        from_date = datetime(date.year, date.month, 1)
        last_day_of_month = monthrange(date.year, date.month)[1]
        to_date = datetime(date.year, date.month, last_day_of_month)
        return badgebox.get_records(from_date, to_date)
