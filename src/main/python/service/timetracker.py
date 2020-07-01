# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime

from typing import cast, Dict, List, Optional

from PyQt5 import QtCore

from config import HelperType
from organization import Organization
from server.jira import Worklog


class Timetracker:
    org: Organization

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def worklogs_to_html(
        self,
        worklogs_by_user: Dict[str, List[Worklog]],
        users: Optional[List[str]] = None,
    ) -> str:
        params = cast(Dict[str, str], self.helper["parameters"])
        html = "<body>"
        if not users:
            users = params["jira_users"].split(",")
        for i, username in enumerate(users):
            if i > 0:
                html += "<hr>"
            total_h = 0.0
            html += "<br><h1>{}</h1><br>".format(username)
            html += '<table border="1" style="font-size: 12px">'
            html += "<tr><th>Issue</th><th>Summary</th><th>Time</th><th>Author</th><th>Started</th><th>Comment</th></tr>"
            worklogs = worklogs_by_user[username]
            for worklog in sorted(worklogs, key=lambda w: w.started):
                total_h += worklog.duration
                html += "<tr>"
                html += f'<td style="padding: 5px">{worklog.ticket}</td>'
                html += f'<td style="padding: 5px">{worklog.summary}</td>'
                html += f'<td style="padding: 5px; text-align: right">{worklog.duration}</td>'
                html += f'<td style="padding: 5px">{worklog.author}</td>'
                html += (
                    f'<td style="padding: 5px">{worklog.started.strftime("%H:%M")}</td>'
                )
                # started.replace(".000+0000", "").replace("T", " ") + " UTC"
                html += '<td style="padding: 5px">{}</td>'.format(worklog.description)
                html += "</tr>\n"
            html += "</table>"
            html += '<br><h4 style="font-size: 16px">Total hours: {}</h4><br>'.format(
                total_h
            )
        html += "</body>"
        return html

    def get_worklogs(
        self,
        date: datetime,
        progress_signal: Optional[QtCore.pyqtSignal] = None,
        users: Optional[List[str]] = None,
    ) -> Dict[str, List[Worklog]]:
        def hours(seconds):
            return seconds / 3600.0

        params = cast(Dict[str, str], self.helper["parameters"])
        worklogs_by_user = {}
        date_str = date.strftime("%Y-%m-%d")
        jira = self.org.jira()
        tickets = jira.search_ticket_by_worklog_date(date)
        worklogs_cache = {}
        if not users:
            users = params["jira_users"].split(",")
        progress_value = 0
        if progress_signal:
            progress_signal.emit(progress_value, len(users) * len(tickets["issues"]))
        for i, username in enumerate(users):
            worklogs = []
            for ticket in tickets["issues"]:
                # Unfortunately the Jira API puts only 20 worklogs at most within
                # a ticket enquiry JSON result, otherwise the following line would
                # have been more than enough:
                # wklogs = ticket["fields"]["worklog"]["worklogs"]
                if not ticket["key"] in worklogs_cache:
                    worklogs_cache[ticket["key"]] = jira.search_worklogs_by_ticket(
                        ticket["key"]
                    )
                for worklog in worklogs_cache[ticket["key"]]["worklogs"]:
                    author = worklog["updateAuthor"]["key"]
                    if author != username:
                        continue
                    if not worklog["started"].startswith(date_str):
                        continue
                    wkobj = Worklog(
                        ticket["key"],
                        author,
                        worklog["comment"],
                        datetime.strptime(
                            worklog["started"], "%Y-%m-%dT%H:%M:%S.000+0000"
                        ),
                        hours(worklog["timeSpentSeconds"]),
                        ticket["fields"]["summary"],
                    )
                    wkobj.self_ = worklog["self"]
                    worklogs.append(wkobj)
                if progress_signal:
                    progress_value += 1
                    progress_signal.emit(
                        progress_value, len(users) * len(tickets["issues"])
                    )
            worklogs_by_user[username] = worklogs
        return worklogs_by_user
