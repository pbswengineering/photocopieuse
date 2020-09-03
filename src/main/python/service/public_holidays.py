# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime, timedelta


class PublicHolidays:
    """
    Computes Italian public holidays.
    """

    def calc_easter(self, year: int) -> datetime:
        """
        An implementation of Butcher's Algorithm for determining the date of
        Easter for the Western church. Works for any date in the Gregorian
        calendar (1583 and onward).
        Borrowed from https://code.activestate.com/recipes/576517-calculate-easter-western-given-a-year/
        """
        a = year % 19
        b = year // 100
        c = year % 100
        d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
        e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
        f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
        month = f // 31
        day = f % 31 + 1
        return datetime(year, month, day)

    def is_italian_public_holiday(self, now: datetime) -> bool:
        """
        Checks whether or not the given date is an Italian public holiday.
        """
        md = (now.month, now.day)
        if md in [
            (1, 1),
            (1, 6),
            (4, 25),
            (5, 1),
            (6, 2),
            (8, 15),
            (11, 1),
            (12, 8),
            (12, 25),
            (12, 26),
        ]:
            return True
        else:
            easter = self.calc_easter(now.year)
            easter_monday = easter + timedelta(days=1)
            return md in [
                (easter.month, easter.day),
                (easter_monday.month, easter_monday.day),
            ]

    def is_terni_saint_patron(self, now: datetime) -> bool:
        """
        Checks whether the given date is Terni's saint patron day, St. Valentine
        (February 14).
        """
        return now.month == 2 and now.day == 14
