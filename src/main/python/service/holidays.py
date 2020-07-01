# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale
from datetime import datetime
import os
from typing import cast, Dict

from bs4 import BeautifulSoup
from pdfrw import PdfReader, PdfWriter

from config import HelperType
from organization import Organization
from server.templating import Templating


class Holidays:
    """
    Holidays request generator.
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def create_holiday_request(
        self,
        request_type: int,
        description: str,
        date: datetime,
        p_day: datetime,
        p_beginning: datetime,
        p_ending: datetime,
        d_day: datetime,
        md_beginning: datetime,
        md_ending: datetime,
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            now = datetime.now()
            datetime_str = date.strftime("%Y-%m-%d") + "_" + now.strftime("%H-%M-%S")
            # Since the description will be used between parentheses, ensure that
            # it starts with a lower case letter and that it doesn't have a trailing
            # full stop.
            description = description[0].lower() + description[1:]
            if description.endswith("."):
                description = description[:-1]
            if request_type == 0:
                file_name = f"{params['pdf_prefix']}_richiesta_permesso_{datetime_str}"
                p_chosen = "☑"
                d_chosen = "☐"
                md_chosen = "☐"
                p_day_str = p_day.strftime("%A %d/%m/%Y").lower()
                p_beginning_str = p_beginning.strftime("%H:%M")
                p_ending_str = p_ending.strftime("%H:%M")
                d_beginning_str = (
                    md_beginning_str
                ) = md_ending_str = ".................."
                confluence_desc = f"Richiesta permesso per {p_day_str}, {p_beginning_str}-{p_ending_str} ({description})"
            elif request_type == 1:
                file_name = f"{params['pdf_prefix']}_richiesta_ferie_{datetime_str}"
                p_chosen = "☐"
                d_chosen = "☑"
                md_chosen = "☐"
                p_day_str = (
                    p_beginning_str
                ) = (
                    p_ending_str
                ) = md_beginning_str = md_ending_str = ".................."
                d_beginning_str = d_day.strftime("%A %d/%m/%Y").lower()
                confluence_desc = (
                    f"Richiesta ferie per {d_beginning_str} ({description})"
                )
            else:
                file_name = f"{params['pdf_prefix']}_richiesta_ferie_{datetime_str}"
                p_chosen = "☐"
                d_chosen = "☐"
                md_chosen = "☑"
                p_day_str = (
                    p_beginning_str
                ) = p_ending_str = d_beginning_str = ".................."
                md_beginning_str = md_beginning.strftime("%A %d/%m/%Y").lower()
                md_ending_str = md_ending.strftime("%A %d/%m/%Y").lower()
                confluence_desc = f"Richiesta ferie da {md_beginning_str} a {md_ending_str} ({description})"
            date_str = date.strftime("%A %d/%m/%Y").lower()
        values = {
            "date": date_str,
            "p_chosen": p_chosen,
            "d_chosen": d_chosen,
            "md_chosen": md_chosen,
            "p_day": p_day_str,
            "p_beginning": p_beginning_str,
            "p_ending": p_ending_str,
            "d_day": d_beginning_str,
            "md_beginning": md_beginning_str,
            "md_ending": md_ending_str,
        }
        templating = Templating()
        template = params["odt_template"].replace("${HOME}", os.environ["HOME"])
        file_path = os.path.join(os.getenv("HOME"), file_name)  # type: ignore
        file_path_odt = file_path + ".odt"
        file_path_pdf = file_path + ".pdf"
        templating.render_template(template, file_path_odt, values, True)
        trailer = PdfReader(file_path_pdf)
        trailer.Info.Producer = "Photocopieuse"
        trailer.Info.Creator = "Photocopieuse"
        trailer.Info.Author = params["employee"]
        trailer.Info.Title = "Richiesta permesso/ferie"
        PdfWriter(file_path_pdf, trailer=trailer).write()
        #
        # Update the Holidays page within Confluence
        #
        confluence = self.org.confluence()
        page_space = params["confluence_space"]
        page_title = params["holidays_page"]
        page_id = confluence.get_page_id(page_space, page_title)
        if not page_id:
            raise Exception(f"Confluence page not found: {page_space} / {page_title}")
        page_body = confluence.get_page_body(page_id)
        soup = BeautifulSoup(page_body, "html.parser")
        date_str = date.strftime("%Y-%m-%d")
        row = BeautifulSoup(
            f"""<tr>
<td>{date_str}</td>
<td>{confluence_desc}</td>
<td>
  <ac:link>
    <ri:attachment ri:filename="{file_name + '.pdf'}" />
    <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
  </ac:link>
</td>
""",
            "html.parser",
        )
        tbody = soup.find_all("tbody")[0]
        tbody.insert(0, row)
        confluence.update_page(page_id, page_title, str(soup))
        confluence.attach_file(file_path_pdf, "application/pdf", page_id)
