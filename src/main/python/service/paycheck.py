# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale
from datetime import datetime
import locale
from typing import cast, Dict

from bs4 import BeautifulSoup

from config import HelperType
from organization import Organization
from utils import change_locale, dirjoin


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
        type_: int,
        pdf: str,
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            if type_ == 1:
                extra = "_13a"
                day_str = "13a " + day.strftime("%Y")
            elif type_ == 2:
                extra = "_14a"
                day_str = "14a " + day.strftime("%Y")
            else:
                extra = ""
                day_str = day.strftime("%b %Y").lower()
            file_name = (
                params["pdf_prefix"]
                + "busta_paga_"
                + day.strftime("%Y-%m")
                + extra
                + ".pdf"
            )
            phab = self.org.phabricator()
            #
            # Upload the attachment to Phabricator
            #
            phab_file_name = dirjoin(params["paycheck_page"], file_name)
            file_phid = phab.upload_file(pdf, phab_file_name)
            file = phab.get_file_by_phid(file_phid)
            #
            # Update the Paycheck page within Phriction
            #
            page_path = params["paycheck_page"]
            page = phab.search_document_by_path(page_path, include_body=True)
            if not page:
                raise Exception(f"Wiki page not found {page_path}")
            page_title = page["attachments"]["content"]["title"]
            page_body = page["attachments"]["content"]["content"]["raw"]
            soup = BeautifulSoup(page_body, features="html.parser")
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
    <td>[[ /F{file['id']} | Download ]]</td>
    """,
                features="html.parser",
            )
            tbody = soup.find_all("table")[0]
            tbody.insert(2, row)
            phab.update_page(page_path, page_title, str(soup))
