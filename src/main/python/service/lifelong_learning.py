# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale
from datetime import datetime
from typing import cast, Dict

from bs4 import BeautifulSoup

from config import HelperType
from organization import Organization
from utils import ita_weekday


class LifelongLearning:
    """
    Automation of Lifelong Learning-related activities (Jira ticket,
    calendar event, confluence pages - detail and yearly summary).
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def _ensure_detail_page(
        self,
        code: str,
        title: str,
        location: str,
        credits: int,
        beginning: datetime,
        ending: datetime,
        notes: str,
        ticket_key: str,
    ) -> str:
        """
        Check whether or not the detail page exists. If it doesn't exist,
        create it.
        """
        params = cast(Dict[str, str], self.helper["parameters"])
        phab = self.org.phabricator()
        #
        # Create or update the detail page
        #
        page_title = f"{title}{params['page_suffix']}"
        page_url = phab.urlize(f"{params['path_prefix']}{beginning.year}/{title}")
        page = phab.search_document_by_path(page_url)
        if not page:
            date_format = " %d %B %Y, %H.%M"
            with different_locale("it_IT"):  # type: ignore
                beginning_str = ita_weekday(beginning) + beginning.strftime(date_format)
                ending_str = ita_weekday(ending) + ending.strftime(date_format)
            plural = credits == 1 and "o" or "i"
            page_body = f"""**Maniphest task:** {ticket_key}

La partecipazione all'evento vale {credits} credit{plural} formativ{plural}.

== Logistica ==
**Luogo:** {location}
**Inizio:** {beginning_str}
**Fine:** {ending_str}

{notes}"""
            page = phab.create_page(page_url, page_title, page_body)
        ###
        ### Update the table in the parent page
        ###
        year = beginning.year
        parent_page_title = f"{year}{params['page_suffix']}"
        parent_page_path = f"{params['path_prefix']}{beginning.year}"
        parent_page = phab.search_document_by_path(parent_page_path, include_body=True)
        parent_page_body = parent_page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(parent_page_body, features="html.parser")
        with different_locale("it_IT"):  # type: ignore
            date_str = beginning.strftime("%Y-%m-%d")
        row = BeautifulSoup(
            f"""<tr>
<td>{code}</td>
<td>[[{page_url} | {title}]]</td>
<td>{date_str}</td>
<td>{location}</td>
<td>{credits}</td>
<td></td>
</tr>""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.append(row)
        phab.update_page(parent_page_path, parent_page_title, str(soup))
        return page

    def _ensure_yearly_summary(self, beginning: datetime) -> str:
        """
        Checks whether the yearly summary page exists. If it doesn't
        exist, create it.
        """
        params = cast(Dict[str, str], self.helper["parameters"])
        phab = self.org.phabricator()
        year = beginning.year
        yearly_summary_path = f"{params['path_prefix']}{year}"
        yearly_summary_page = phab.search_document_by_path(yearly_summary_path)
        if yearly_summary_page:
            return yearly_summary_page["phid"]
        yearly_summary_body = f"""
= Per il {year + 1} =

== Apprendimento non formale ==

Ho partecipato ai seguenti eventi, accreditati dalla segreteria:

<table>
    <tr>
        <th>Codice</th>
        <th>Nome</th>
        <th>Data</th>
        <th>Luogo</th>
        <th>Crediti</th>
        <th>Attestato</th>
    </tr>
</table>

== Apprendimento informale ==

Ho partecipato a questi eventi:

<table>
    <tr>
        <th>Nome</th>
        <th>Data</th>
        <th>Luogo</th>
        <th>Note</th>
    </tr>
</table>

Ho seguito questi corsi online:

<table>
    <tr>
        <th>Nome</th>
        <th>Fornitore</th>
        <th>Data</th>
        <th>Note</th>
    </tr>
</table>

Ho letto queste cose:

<table>
    <tr>
        <th>Nome</th>
        <th>Data</th>
    </tr>
</table>
"""
        yearly_summary_title = f"{year}{params['page_suffix']}"
        create_res = phab.create_page(
            yearly_summary_path, yearly_summary_title, yearly_summary_body
        )
        return create_res["phid"]

    def schedule(
        self,
        code: str,
        title: str,
        location: str,
        beginning: datetime,
        ending: datetime,
        credits: int,
        notes: str,
    ):
        """
        Create a Maniphest ticket and a calendar event for a lifelong learning task.
        """
        #
        # Create the Maniphest ticket
        #
        params = cast(Dict[str, str], self.helper["parameters"])
        date_format = "%A %d %B %Y, %H.%M"
        beginning_str = beginning.strftime(date_format)
        ending_str = ending.strftime(date_format)
        description = f"""* **Location:** {location}
* **From:** {beginning_str}
* **To:** {ending_str}
* **Credits:** {credits}"""
        phab = self.org.phabricator()
        fields = {
            "issuetype_field_name": params["phabricator_issuetype_field"],
            "issuetype_field_value": params["phabricator_issuetype_value"],
            "description": description,
            "project": params["phabricator_project"],
            "summary": title,
            "assignee": phab.user_phid,
            "credits_field_name": params["phabricator_credits_field"],
            "credits_field_value": credits,
            "language_field_name": params["phabricator_language_field"],
            "language_field_value": params["phabricator_language_value"],
        }
        result = phab.create_ticket(fields)
        ticket_key = "T" + result["id"]
        ticket_phid = result["phid"]
        #
        # Create the calendar event
        #
        cal = self.org.calendar()
        calendar_summary = cal.filter_text(f"{ticket_key} {title}")
        calendar_location = cal.filter_text(location)
        cal.add_event(calendar_summary, calendar_location, beginning, ending, "-PT1H")
        #
        # Create the Phriction pages
        #
        self._ensure_yearly_summary(beginning)
        page = self._ensure_detail_page(
            code,
            title,
            location,
            credits,
            beginning,
            ending,
            notes,
            ticket_key,
        )
        #
        # Update the Maniphest ticket wiki URL
        #
        phab.update_ticket_fields(
            ticket_phid,
            (
                (params["phabricator_wiki_field"], phab.wiki_url + page["slug"]),  # noqa
                (params["phabricator_start_field"], int(beginning.timestamp())),
                (params["phabricator_end_field"], int(ending.timestamp())),
            ),
        )
