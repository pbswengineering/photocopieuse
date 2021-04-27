# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import base64
import logging
import os
import re
import time
from typing import Optional

import phabricator
from PyQt5 import QtCore
import requests

from utils import dirjoin, sha256


class Phabricator:
    """
    Generic Phabricator server.
    """

    url: str
    api_url: str
    wiki_url: str
    token: str
    user_phid: str
    phab: phabricator.Phabricator

    PRIO_NORMAL = 50

    def __init__(self, url: str, user_phid: str, token: str):
        self.url = url
        self.api_url = dirjoin(url, "api/")
        self.wiki_url = dirjoin(url, "w/")
        self.token = token
        self.user_phid = user_phid
        self.phab = phabricator.Phabricator(host=self.api_url, token=token, timeout=60)

    def urlize(self, title: str):
        url = title.strip()
        url = url.replace("-", " ")
        url = url.replace("&", " ")
        url = url.replace("'", " ")
        url = re.sub(r"\s+", " ", url)
        url = url.replace("\\", "/")
        url = url.replace(",", "")
        url = url.replace(".", "")
        url = url.replace("(", "")
        url = url.replace(")", "")
        url = url.replace("à", "a")
        url = url.replace("è", "e")
        url = url.replace("é", "e")
        url = url.replace("ì", "i")
        url = url.replace("ù", "u")
        url = url.replace(" ", "_")
        if len(url) > 127:  # Maximum slug length as per Phriction's DB
            url = url[:125]  # Leave some characters for numerical prefixes (_XX)
        return url

    def search_document_by_path(self, path: str, include_body=False):
        if not path.endswith("/"):
            path += "/"
        s = requests.Session()
        data = {"api.token": self.token}
        data["constraints[paths][0]"] = path
        if include_body:
            data["attachments[content]"] = "true"
        url = dirjoin(self.api_url, "phriction.document.search")
        req = requests.Request("POST", url, data=data)
        prepped = s.prepare_request(req)
        resp = s.send(prepped)
        resp.raise_for_status()
        resp_json = resp.json()
        try:
            return resp_json["result"]["data"][0]
        except Exception as e:
            logging.error("phabricator.search_document_by_path exception")
            logging.error(e)
            logging.error(f"JSON response:\n{resp_json}")
            return None

    def create_page(self, slug: str, title: str, content: str):
        return self.phab.phriction.create(slug=slug, title=title, content=content)

    def update_page(self, slug: str, title: str, content: str):
        return self.phab.phriction.edit(slug=slug, title=title, content=content)

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

    def update_ticket_fields(self, task_phid: str, transaction_tuples):
        transactions = [{"type": t[0], "value": t[1]} for t in transaction_tuples]
        return self.phab.maniphest.edit(
            objectIdentifier=task_phid, transactions=transactions
        )

    def upload_file(self, fpath: str, name: str, progress_signal: Optional[QtCore.pyqtSignal] = None):
        if progress_signal:
            progress_signal.emit(0, 100)
        length = os.path.getsize(fpath)
        hash = sha256(fpath)
        res = self.phab.file.allocate(name=name, contentLength=length, contentHash=hash)
        phid = res["filePHID"]
        if phid is None and "error" not in res:
            with open(fpath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                res = self.phab.file.upload(data_base64=b64, name=name)
                if progress_signal:
                    progress_signal.emit(100, 100)
                return "".join(res.keys())
        elif phid is not None:
            with open(fpath, "rb") as f:
                neededChunks = self.phab.file.querychunks(filePHID=phid)
                for i, neededChunk in enumerate(neededChunks):
                    if not neededChunk["complete"]:
                        bstart = int(neededChunk["byteStart"])
                        bend = int(neededChunk["byteEnd"])
                        f.seek(bstart)
                        chunk = f.read(bend - bstart)
                        b64 = base64.b64encode(chunk).decode("utf-8")
                        for attempt in range(3):
                            try:
                                res = self.phab.file.uploadchunk(
                                    filePHID=phid,
                                    byteStart=bstart,
                                    data=b64,
                                    dataEncoding="base64",
                                )
                                break
                            except:  # noqa
                                time.sleep(5)
                    if progress_signal:
                        progress_signal.emit(i + 1, len(neededChunks))
                return phid
        else:
            logging.error(f"Error: {res['error']}")
            return None

    def get_file_by_phid(self, file_phid: str):
        res = self.phab.file.search(constraints={"phids": [file_phid]})
        if res["data"]:
            return res["data"][0]
        else:
            return None
