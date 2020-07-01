# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime

import atlassian


class Worklog:
    ticket: str
    summary: str
    author: str
    description: str
    started: datetime
    duration: float
    self_: str

    def __init__(
        self,
        ticket: str,
        author: str,
        description: str,
        started: datetime,
        duration: float,
        summary="",
    ):
        self.ticket = ticket
        self.summary = summary
        self.author = author
        self.description = description
        self.started = started
        self.duration = duration
        self.self_ = ""

    def __repr__(self):
        return f"Worklog({self.ticket}, {self.summary} {self.author}, {self.description[:20]}, {self.started} {self.duration})"


class Jira:
    """
    Generic Jira server.
    """

    url: str
    username: str
    jira: atlassian.Jira

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.jira = atlassian.Jira(url=url, username=username, password=password)

    def create_ticket(self, fields):
        return self.jira.issue_create(fields)

    def search_ticket_by_summary(self, summary: str):
        jql = f'summary ~ "{summary}"'
        return self.jira.jql(jql)

    def search_ticket_by_worklog_date(self, date: datetime):
        jql = "worklogDate = {}".format(date.strftime("%Y-%m-%d"))
        return self.jira.jql(jql)

    def search_worklogs_by_ticket(self, ticket_key: str):
        return self.jira.issue_get_worklog(ticket_key)

    def create_confluence_link(
        self,
        ticket_key: str,
        confluence_page_url: str,
        link_title: str,
        confluence_name: str,
        confluence_id: str,
        page_id: str,
    ):
        url = f"rest/api/2/issue/{ticket_key}/remotelink"
        data = {
            "globalId": f"appId={confluence_id}&pageId={page_id}",
            "application": {
                "type": "com.atlassian.confluence",
                "name": confluence_name,
            },
            "relationship": "Wiki Page",
            "object": {"url": confluence_page_url, "title": link_title},
        }
        return self.jira.post(url, data=data)

    def add_worklog(self, worklog: Worklog):
        self.jira.issue_worklog(
            worklog.ticket,
            worklog.started.strftime("%Y-%m-%dT%H:%M:%S.000+0000%z"),
            int(worklog.duration * 3600),
            worklog.description,
        )

    def delete_worklog(self, worklog: Worklog):
        if not worklog.self_:
            return
        url = worklog.self_
        if url.startswith(self.url):
            url = url[len(self.url) :]
        if not url.startswith("/"):
            url = "/" + url
        return self.jira.delete(url)
