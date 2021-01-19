# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import phabricator


class Phabricator:
    """
    Generic Phabricator server.
    """

    url: str
    user_phid: str
    phab: phabricator.Phabricator

    PRIO_NORMAL = 50

    def __init__(self, url: str, user_phid: str, token: str):
        self.url = url
        self.user_phid = user_phid
        self.phab = phabricator.Phabricator(host=url, token=token)

    def create_ticket(self, fields):
        title = fields["summary"]
        description = fields["description"]
        owner_phid = fields["assignee"]
        project_phid = fields["project"]
        res = self.phab.maniphest.createtask(
            title=title,
            description=description,
            ownerPHID=owner_phid,
            projectPHIDs=[project_phid],
            priority=self.PRIO_NORMAL,
        )
        task_phid = res["phid"]
        transactions = [{"type": "status", "value": "open"}]
        if "issuetype_field_name" in fields and "issuetype_field_value" in fields:
            transactions.append(
                {
                    "type": fields["issuetype_field_name"],
                    "value": fields["issuetype_field_value"],
                }
            )
        if "language_field_name" in fields and "language_field_value" in fields:
            transactions.append(
                {
                    "type": fields["language_field_name"],
                    "value": fields["language_field_value"],
                }
            )
        if "credits_field_name" in fields and "credits_field_value" in fields:
            transactions.append(
                {
                    "type": fields["credits_field_name"],
                    "value": str(fields["credits_field_value"]),
                }
            )
        self.phab.maniphest.edit(objectIdentifier=task_phid, transactions=transactions)
        return res
