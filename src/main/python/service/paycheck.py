# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale
from datetime import datetime
import locale
import os
from typing import cast, Dict

from bs4 import BeautifulSoup

from config import HelperType
from organization import Organization
from utils import change_locale


class Paycheck:
    """
    Paycheck uploader.
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def upload_paycheck(
        self,
        day: datetime,
        hours: float,
        overtime: float,
        gross: float,
        net: float,
        holidays: float,
        festivities: float,
        permits: float,
        pdf: str,
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            day_str = day.strftime("%b %Y").lower()
            file_name = (
                params["pdf_prefix"] + "busta_paga_" + day.strftime("%Y-%m") + ".pdf"
            )
            #
            # Update the Paycheck page within Confluence
            #
            confluence = self.org.confluence()
            page_space = params["confluence_space"]
            page_title = params["paycheck_page"]
            page_id = confluence.get_page_id(page_space, page_title)
            if not page_id:
                raise Exception(
                    f"Confluence page not found: {page_space} / {page_title}"
                )
            page_body = confluence.get_page_body(page_id)
            soup = BeautifulSoup(page_body, "html.parser")
            with change_locale("de_DE"):
                hours_str = locale.format_string("%.2f", hours)
                if overtime > 0:
                    overtime_str = locale.format_string("%.2f", overtime)
                else:
                    overtime_str = "-"
                gross_str = locale.format_string("%.2f", gross)
                net_str = locale.format_string("%.2f", net)
                holidays_str = locale.format_string("%.2f", holidays)
                festivities_str = locale.format_string("%.2f", festivities)
                permits_str = locale.format_string("%.2f", permits)
            row = BeautifulSoup(
                f"""<tr>
    <td>{day_str}</td>
    <td>{hours_str}</td>
    <td>{overtime_str}</td>
    <td>€ {gross_str}</td>
    <td>€ {net_str}</td>
    <td>{holidays_str}</td>
    <td>{festivities_str}</td>
    <td>{permits_str}</td>
    <td>
      <ac:link>
        <ri:attachment ri:filename="{file_name}" />
        <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
      </ac:link>
    </td>
    """,
                "html.parser",
            )
            tbody = soup.find_all("tbody")[0]
            tbody.insert(0, row)
            confluence.update_page(page_id, page_title, str(soup))
            new_pdf_path = os.path.join(os.path.dirname(pdf), file_name)
            os.rename(pdf, new_pdf_path)
            confluence.attach_file(new_pdf_path, "application/pdf", page_id)
