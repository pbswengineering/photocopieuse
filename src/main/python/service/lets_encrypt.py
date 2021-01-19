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


class LetsEncrypt:
    """
    Automation of the activities required to renew a Let's Encrypt
    certificate (Jira task and calendar event).
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def schedule(self, date: datetime):
        """
        Create the Jira task and the calendar event for diffie's Let's Encrypt
        certificate renewal.

        The certificate expires after 90 days.
        """
        #
        # Jira ticket creation
        #
        params = cast(Dict[str, str], self.helper["parameters"])
        date_str = date.strftime("%A %d %B %Y, %H.%M")
        summary = f"Let's Encrypt renewal (expires on {date_str})"
        description = f"Renew {params['hostname']}'s Let's Encrypt certificate, as it expires on {date_str}"
        phab = self.org.phabricator()
        fields = {
            "issuetype_field_name": params["phabricator_issuetype_field"],
            "issuetype_field_value": params["phabricator_issuetype_value"],
            "description": description,
            "project": params["phabricator_project"],
            "summary": summary,
            "assignee": phab.user_phid,
            "language_field_name": params["phabricator_language_field"],
            "language_field_value": params["phabricator_language_value"],
        }
        result = phab.create_ticket(fields)
        ticket_key = "T" + result["id"]
        #
        # Create the calendar event
        #
        calendar = self.org.calendar()
        calendar_summary = (
            f"{ticket_key}: Let's Encrypt renewal (expires on {date_str})"
        )
        calendar_summary = calendar.filter_text(calendar_summary)
        date_calendier = date - timedelta(days=10)
        beginning = datetime(
            date_calendier.year, date_calendier.month, date_calendier.day, 10, 0, 0
        )
        ending = datetime(
            date_calendier.year, date_calendier.month, date_calendier.day, 11, 0, 0
        )
        calendar.add_event(calendar_summary, "", beginning, ending, "P0TS")
