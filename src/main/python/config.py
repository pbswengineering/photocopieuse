# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import json
import os
from typing import Dict, List, Union

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from organization import Organization
from server.badgebox import BadgeBox
from server.caldav import CalDAV
from server.confluence import Confluence
from server.phabricator import Phabricator
from server.jira import Jira
from server.smtp import SMTP
from server.ftp import FTP

HelperType = Dict[str, Union[str, int, bool, Dict[str, str]]]


class Config:
    config_file: str
    json: Dict
    _organizations: Dict[str, Organization]

    def __init__(self, qapp: QApplication):
        self._organizations = {}
        config_file_store = os.path.join(os.path.expanduser("~"), ".photocopieuse")
        config_json_found = False
        if os.path.exists(config_file_store):
            with open(config_file_store) as cfs:
                self.config_file = cfs.read().strip()
                if os.path.exists(self.config_file):
                    config_json_found = True
        if not config_json_found:
            self.config_file = QFileDialog.getOpenFileName(
                None,
                "Open config.json file",
                os.path.expanduser("~"),
                "JSON files (*.json)",
            )[0]
            if not self.config_file:
                QMessageBox.critical(
                    None,
                    "Photocopieuse",
                    "In order to run Photocopieuse you need to select a suitable config.json file.",
                )
                qapp.quit()
            with open(config_file_store, "w") as cfs:
                cfs.write(self.config_file)
        with open(self.config_file) as cf:
            self.json = json.load(cf)

    def organizations(self) -> List[Organization]:
        return [self.organization(name) for name in self.json["organizations"].keys()]

    def organization(self, name) -> Organization:
        if name in self._organizations:
            return self._organizations[name]
        org = Organization(name)
        oj = self.json["organizations"][name]
        if "server_jira" in oj:
            oj_jira = oj["server_jira"]
            org.set_jira(Jira(oj_jira["url"], oj_jira["username"], oj_jira["password"]))
        if "server_confluence" in oj:
            oj_confluence = oj["server_confluence"]
            org.set_confluence(
                Confluence(
                    oj_confluence["url"],
                    oj_confluence["username"],
                    oj_confluence["password"],
                    oj_confluence["global_identifier"],
                    oj_confluence["name"],
                )
            )
        if "server_phabricator" in oj:
            oj_phabricator = oj["server_phabricator"]
            org.set_phabricator(
                Phabricator(
                    oj_phabricator["url"],
                    oj_phabricator["user_phid"],
                    oj_phabricator["token"],
                )
            )
        if "server_calendar" in oj:
            oj_cal = oj["server_calendar"]
            org.set_calendar(
                CalDAV(oj_cal["url"], oj_cal["username"], oj_cal["password"])
            )
        if "server_badgebox" in oj:
            oj_badge = oj["server_badgebox"]
            org.set_badgebox(BadgeBox(oj_badge["username"], oj_badge["password"]))
        if "server_smtp" in oj:
            oj_smtp = oj["server_smtp"]
            org.set_smtp(
                SMTP(
                    oj_smtp["address"],
                    oj_smtp["port"],
                    oj_smtp["username"],
                    oj_smtp["password"],
                    oj_smtp["default_from_address"],
                    oj_smtp["html_signature"],
                )
            )
        if "server_ftp" in oj:
            oj_ftp = oj["server_ftp"]
            org.set_ftp(
                FTP(
                    oj_ftp["host"],
                    oj_ftp["port"],
                    oj_ftp["username"],
                    oj_ftp["password"],
                )
            )
        self._organizations[name] = org
        return org

    def helpers(self) -> List[HelperType]:
        return self.json["helpers"]
