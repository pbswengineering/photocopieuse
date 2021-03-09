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
from utils import dirjoin, ita_weekday, replace_path_vars


class Holidays:
    """
    Holiday request generator.
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def day_to_ita_str(self, day: datetime) -> str:
        return f"{ita_weekday(day)} {day.strftime('%d/%m/%Y')}".lower()

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
                p_day_str = self.day_to_ita_str(p_day)
                p_beginning_str = p_beginning.strftime("%H:%M")
                p_ending_str = p_ending.strftime("%H:%M")
                d_beginning_str = (
                    md_beginning_str
                ) = md_ending_str = ".................."
                wiki_desc = f"Richiesta permesso per {p_day_str}, {p_beginning_str}-{p_ending_str} ({description})"
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
                d_beginning_str = self.day_to_ita_str(d_day)
                wiki_desc = f"Richiesta ferie per {d_beginning_str} ({description})"
            else:
                file_name = f"{params['pdf_prefix']}_richiesta_ferie_{datetime_str}"
                p_chosen = "☐"
                d_chosen = "☐"
                md_chosen = "☑"
                p_day_str = (
                    p_beginning_str
                ) = p_ending_str = d_beginning_str = ".................."
                md_beginning_str = self.day_to_ita_str(md_beginning)
                md_ending_str = self.day_to_ita_str(md_ending)
                wiki_desc = f"Richiesta ferie da {md_beginning_str} a {md_ending_str} ({description})"
            date_str = self.day_to_ita_str(date)
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
        template = replace_path_vars(params["odt_template"])
        file_path = os.path.join(os.path.expanduser("~"), file_name)  # type: ignore
        file_path_odt = file_path + ".odt"
        file_path_pdf = file_path + ".pdf"
        templating.render_template(template, file_path_odt, values, True)
        trailer = PdfReader(file_path_pdf)
        trailer.Info.Producer = "Photocopieuse"
        trailer.Info.Creator = "Photocopieuse"
        trailer.Info.Author = params["employee"]
        trailer.Info.Title = "Richiesta permesso/ferie"
        PdfWriter(file_path_pdf, trailer=trailer).write()
        phab = self.org.phabricator()
        #
        # Upload the attachment to Phabricator
        #
        phab_file_name = dirjoin(params["holidays_page"], file_name) + ".pdf"
        file_phid = phab.upload_file(file_path_pdf, phab_file_name)
        file = phab.get_file_by_phid(file_phid)
        #
        # Update the Holidays wiki page
        #
        page_path = params["holidays_page"]
        page = phab.search_document_by_path(page_path, include_body=True)
        if not page:
            raise Exception(f"Wiki page not found {page_path}")
        page_title = page["attachments"]["content"]["title"]
        page_body = page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(page_body, "html.parser")
        date_str = date.strftime("%Y-%m-%d")
        row = BeautifulSoup(
            f"""<tr>
<td>{date_str}</td>
<td>{wiki_desc}</td>
<td>[[ /F{file['id']} | Download ]]</td>
</tr>""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.insert(2, row)
        phab.update_page(page_path, page_title, str(soup))
