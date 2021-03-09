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
from typing import cast, Dict, List

from bs4 import BeautifulSoup

from config import HelperType
from organization import Organization
from utils import change_locale, concatenate_pdfs, dirjoin


class Bills:
    """
    Household bills manager.
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def upload_telephone(
        self,
        t_due_date: datetime,
        t_month: datetime,
        t_amount: float,
        t_notes: str,
        pdf_files: List[str],
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            month_str = t_month.strftime("%Y-%m")
            month_str_for_table = t_month.strftime("%B %Y").lower()
            file_name = f"bolletta_{month_str}.pdf"
        phab = self.org.phabricator()
        page_path = params["telephone_page"]
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        phab_file_name = dirjoin(page_path, file_name)
        file_phid = phab.upload_file(new_pdf_path, phab_file_name)
        file = phab.get_file_by_phid(file_phid)
        #
        # Update the specific bill wiki page
        #
        page = phab.search_document_by_path(page_path, include_body=True)
        if not page:
            raise Exception(f"Wiki page not found {page_path}")
        page_title = page["attachments"]["content"]["title"]
        page_body = page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(page_body, features="html.parser")
        due_date_str = t_due_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", t_amount)
        row = BeautifulSoup(
            f"""<tr>
<td>{due_date_str}</td>
<td>{month_str_for_table}</td>
<td>€ {amount_str}</td>
<td>[[ /F{file['id']} | Download ]]</td>
<td>{t_notes}</td>
</tr>
""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.insert(2, row)
        phab.update_page(page_path, page_title, str(soup))

    def upload_electricity(
        self,
        e_due_date: datetime,
        e_interval: str,
        e_amount: float,
        e_notes: str,
        pdf_files: List[str],
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            month_str = e_due_date.strftime("%Y-%m")
            file_name = f"bolletta_{month_str}.pdf"
        phab = self.org.phabricator()
        page_path = params["electricity_page"]
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        phab_file_name = dirjoin(page_path, file_name)
        file_phid = phab.upload_file(new_pdf_path, phab_file_name)
        file = phab.get_file_by_phid(file_phid)
        #
        # Update the specific bill wiki page
        #
        page = phab.search_document_by_path(page_path, include_body=True)
        if not page:
            raise Exception(f"Wiki page not found {page_path}")
        page_title = page["attachments"]["content"]["title"]
        page_body = page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(page_body, features="html.parser")
        due_date_str = e_due_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", e_amount)
        row = BeautifulSoup(
            f"""<tr>
<td>{due_date_str}</td>
<td>{e_interval}</td>
<td>€ {amount_str}</td>
<td>[[ /F{file['id']} | Download ]]</td>
<td>{e_notes}</td>
</tr>
""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.insert(2, row)
        phab.update_page(page_path, page_title, str(soup))

    def upload_gas(
        self,
        g_date: datetime,
        g_interval: str,
        g_amount: float,
        g_cubic_meters: int,
        g_notes: str,
        pdf_files: List[str],
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            month_str = g_date.strftime("%Y-%m")
            file_name = f"bolletta_gas_{month_str}.pdf"
        phab = self.org.phabricator()
        page_path = params["gas_page"]
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        phab_file_name = dirjoin(page_path, file_name)
        file_phid = phab.upload_file(new_pdf_path, phab_file_name)
        file = phab.get_file_by_phid(file_phid)
        #
        # Update the specific bill wiki page
        #
        page = phab.search_document_by_path(page_path, include_body=True)
        if not page:
            raise Exception(f"Wiki page not found {page_path}")
        page_title = page["attachments"]["content"]["title"]
        page_body = page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(page_body, features="html.parser")
        date_str = g_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", g_amount)
        row = BeautifulSoup(
            f"""<tr>
<td>{date_str}</td>
<td>{g_interval}</td>
<td>€ {amount_str}</td>
<td>{g_cubic_meters}</td>
<td>[[ /F{file['id']} | Download ]]</td>
<td>{g_notes}</td>
</tr>
""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.insert(2, row)
        phab.update_page(page_path, page_title, str(soup))

    def upload_water(
        self,
        w_date: datetime,
        w_interval: str,
        w_amount: float,
        w_notes: str,
        pdf_files: List[str],
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            month_str = w_date.strftime("%Y-%m")
            file_name = f"bolletta_acqua_{month_str}.pdf"
        phab = self.org.phabricator()
        page_path = params["water_page"]
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        phab_file_name = dirjoin(page_path, file_name)
        file_phid = phab.upload_file(new_pdf_path, phab_file_name)
        file = phab.get_file_by_phid(file_phid)
        #
        # Update the specific bill wiki page
        #
        page = phab.search_document_by_path(page_path, include_body=True)
        if not page:
            raise Exception(f"Wiki page not found {page_path}")
        page_title = page["attachments"]["content"]["title"]
        page_body = page["attachments"]["content"]["content"]["raw"]
        soup = BeautifulSoup(page_body, features="html.parser")
        date_str = w_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", w_amount)
        row = BeautifulSoup(
            f"""<tr>
<td>{date_str}</td>
<td>{w_interval}</td>
<td>€ {amount_str}</td>
<td>[[ /F{file['id']} | Download ]]</td>
<td>{w_notes}</td>
</tr>
""",
            features="html.parser",
        )
        tbody = soup.find_all("table")[0]
        tbody.insert(2, row)
        phab.update_page(page_path, page_title, str(soup))
