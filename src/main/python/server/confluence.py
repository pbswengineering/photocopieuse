# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from urllib.parse import urljoin

import atlassian


class Confluence:
    """
    Generic Confluence server.
    """

    url: str
    global_identifier: str
    name: str
    confluence: atlassian.Confluence

    def __init__(
        self, url: str, username: str, password: str, global_identifier: str, name: str
    ):
        self.url = url
        self.global_identifier = global_identifier
        self.name = name
        self.confluence = atlassian.Confluence(
            url=url, username=username, password=password
        )

    def get_page_id(self, space: str, title: str) -> str:
        """
        Return the ID of a page, given its space and title.
        """
        return self.confluence.get_page_id(space, title)

    def get_page_url(self, page_id: str) -> str:
        """
        Return the URL of a page, given its ID.
        """
        page = self.confluence.get_page_by_id(page_id)
        webui = page["_links"]["webui"]
        if webui[0] == "/":
            webui = webui[1:]
        url_base = self.url
        if url_base[-1] != "/":
            url_base += "/"
        return urljoin(url_base, webui)

    def create_page(self, space: str, title: str, body: str, parent_page_id: str):
        """
        Create a Confluence page.
        """
        return self.confluence.create_page(space, title, body, parent_page_id)

    def update_page(self, page_id: str, title: str, body: str):
        """
        Update a Confluence page.
        """
        return self.confluence.update_page(page_id, title, body)

    def get_page_body(self, page_id: str) -> str:
        """
        Return the body of the specified page.
        """
        parsed_json = self.confluence.get_page_by_id(page_id, expand="body.view")
        return parsed_json["body"]["view"]["value"]

    def attach_file(self, file: str, mime: str, page_id: str):
        """
        Attach a file to a page.
        """
        self.confluence.attach_file(file, content_type=mime, page_id=page_id)
