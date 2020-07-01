# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import month_name
from datetime import datetime
from typing import cast, Dict

from config import HelperType
from organization import Organization


class CryptoGram:
    """
    Automation of the activities required to publish Crypto-Gram
    in EPUB/MOBI format (creation of the Jira ticket and of the calendar
    event).
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def schedule(self, month: int, year: int):
        """
        Create the Jira task and the calendar event for the publication
        of the Crypto-Gram newsletter for e-readers.

        Crypto-Gram is a newsletter on security published each month
        by Bruce Schneier.
        """
        #
        # Jira ticket creation
        #
        month_str = month_name[month]
        jira_summary = f"Crypto-Gram, {month_str} {year}"
        jira_description = "Crypto-Gram is a famous free monthly newsletter from security expert Bruce Schneier. I publish an edition in EPUB and MOBI format on my website."
        jira = self.org.jira()
        params = cast(Dict[str, str], self.helper["parameters"])
        language_field = params["jira_language_field"]
        fields = {
            "issuetype": {"name": params["jira_issue_type"]},
            "description": jira_description,
            "project": {"key": params["jira_project"]},
            "summary": jira_summary,
            "assignee": {"name": jira.username},
            language_field: {"value": params["jira_language_field_value"]},
        }
        creation_result = jira.create_ticket(fields)
        ticket_key = creation_result["key"]
        #
        # Calendar event creation
        #
        cal = self.org.calendar()
        calendar_summary = f"{ticket_key}: Crypto-Gram, {month_str} - {year}"
        calendar_summary = cal.filter_text(calendar_summary)
        beginning = datetime(year, month, 15, 15, 0, 0)
        ending = datetime(year, month, 15, 16, 0, 0)
        cal.add_event(calendar_summary, "", beginning, ending, "-PT0S")
