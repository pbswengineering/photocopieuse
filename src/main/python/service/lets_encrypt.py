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
        jira_summary = f"Let's Encrypt renewal (expires on {date_str})"
        jira_description = f"Renew {params['hostname']}'s Let's Encrypt certificate, as it expires on {date_str}"
        jira = self.org.jira()
        language_field = params["jira_language_field"]
        fields = {
            "issuetype": {"name": params["jira_issue_type"]},
            "description": jira_description,
            "project": {"key": params["jira_project"]},
            "summary": jira_summary,
            "assignee": {"name": jira.username},
            language_field: {"value": params["jira_language_field_value"]},
        }
        result = jira.create_ticket(fields)
        ticket_key = result["key"]
        #
        # Create a link between the Jira ticket and the confluence
        # page with instructions on how to renew the certificate.
        #
        confluence = self.org.confluence()
        confluence_title = params["howto_page"]
        page_id = confluence.get_page_id(params["confluence_space"], confluence_title)
        page_url = confluence.get_page_url(page_id)
        jira.create_confluence_link(
            ticket_key,
            page_url,
            confluence_title,
            confluence.name,
            confluence.global_identifier,
            page_id,
        )
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
