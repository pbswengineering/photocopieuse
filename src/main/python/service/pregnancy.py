# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime, timedelta
from typing import cast, Dict

from config import HelperType
from organization import Organization


class Pregnancy:
    """
    Pregnancy uploader.
    """

    org: Organization
    helper: HelperType
    lmp: datetime
    edd: datetime
    ga: str
    week: int
    trimester: int

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper
        params = cast(Dict[str, str], self.helper["parameters"])
        self.lmp = datetime.strptime(params["lmp"], "%Y-%m-%d")
        self.edd = self.lmp + timedelta(weeks=40)
        # Gestational age
        today = datetime.now()
        age_days = (today - self.lmp).days
        age_perc = age_days * 100 // (40 * 7)
        age_weeks = (age_days // 7, age_days % 7)
        left_days = (self.edd - today).days
        left_weeks = (left_days // 7, left_days % 7)
        self.ga = "{}+{} ({}%, {}+{} left)".format(
            age_weeks[0], age_weeks[1], age_perc, left_weeks[0], left_weeks[1]
        )
        self.week = age_weeks[0] + 1
        self.trimester = (age_weeks[0] // (4 * 3)) + 1
