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
from utils import change_locale, concatenate_pdfs


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
        confluence = self.org.confluence()
        page_space = params["confluence_space"]
        page_title = params["telephone_page"]
        page_id = confluence.get_page_id(page_space, page_title)
        if not page_id:
            raise Exception(f"Confluence page not found: {page_space} / {page_title}")
        page_body = confluence.get_page_body(page_id)
        soup = BeautifulSoup(page_body, "html.parser")
        due_date_str = t_due_date.strftime("%d/%m/%Y")
        with change_locale("German"):
            amount_str = locale.format_string("%.2f", t_amount)
        row = BeautifulSoup(
            f"""<tr>
<td>{due_date_str}</td>
<td>{month_str_for_table}</td>
<td>€ {amount_str}</td>
<td>
  <ac:link>
    <ri:attachment ri:filename="{file_name}" />
    <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
  </ac:link>
</td>
<td>{t_notes}</td>
</tr>
""",
            "html.parser",
        )
        tbody = soup.find_all("tbody")[0]
        tbody.insert(0, row)
        confluence.update_page(page_id, page_title, str(soup))
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        confluence.attach_file(new_pdf_path, "application/pdf", page_id)

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
        confluence = self.org.confluence()
        page_space = params["confluence_space"]
        page_title = params["electricity_page"]
        page_id = confluence.get_page_id(page_space, page_title)
        if not page_id:
            raise Exception(f"Confluence page not found: {page_space} / {page_title}")
        page_body = confluence.get_page_body(page_id)
        soup = BeautifulSoup(page_body, "html.parser")
        due_date_str = e_due_date.strftime("%d/%m/%Y")
        with change_locale("German"):
            amount_str = locale.format_string("%.2f", e_amount)
        row = BeautifulSoup(
            f"""<tr>
        <td>{due_date_str}</td>
        <td>{e_interval}</td>
        <td>€ {amount_str}</td>
        <td>
          <ac:link>
            <ri:attachment ri:filename="{file_name}" />
            <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
          </ac:link>
        </td>
        <td>{e_notes}</td>
        </tr>
        """,
            "html.parser",
        )
        tbody = soup.find_all("tbody")[0]
        tbody.insert(0, row)
        confluence.update_page(page_id, page_title, str(soup))
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        confluence.attach_file(new_pdf_path, "application/pdf", page_id)

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
        confluence = self.org.confluence()
        page_space = params["confluence_space"]
        page_title = params["gas_page"]
        page_id = confluence.get_page_id(page_space, page_title)
        if not page_id:
            raise Exception(f"Confluence page not found: {page_space} / {page_title}")
        page_body = confluence.get_page_body(page_id)
        soup = BeautifulSoup(page_body, "html.parser")
        date_str = g_date.strftime("%d/%m/%Y")
        with change_locale("German"):
            amount_str = locale.format_string("%.2f", g_amount)
        row = BeautifulSoup(
            f"""<tr>
        <td>{date_str}</td>
        <td>{g_interval}</td>
        <td>€ {amount_str}</td>
        <td>{g_cubic_meters}</td>
        <td>
          <ac:link>
            <ri:attachment ri:filename="{file_name}" />
            <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
          </ac:link>
        </td>
        <td>{g_notes}</td>
        </tr>
        """,
            "html.parser",
        )
        tbody = soup.find_all("tbody")[0]
        tbody.insert(0, row)
        confluence.update_page(page_id, page_title, str(soup))
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        confluence.attach_file(new_pdf_path, "application/pdf", page_id)

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
        confluence = self.org.confluence()
        page_space = params["confluence_space"]
        page_title = params["water_page"]
        page_id = confluence.get_page_id(page_space, page_title)
        if not page_id:
            raise Exception(f"Confluence page not found: {page_space} / {page_title}")
        page_body = confluence.get_page_body(page_id)
        soup = BeautifulSoup(page_body, "html.parser")
        date_str = w_date.strftime("%d/%m/%Y")
        with change_locale("German"):
            amount_str = locale.format_string("%.2f", w_amount)
        row = BeautifulSoup(
            f"""<tr>
        <td>{date_str}</td>
        <td>{w_interval}</td>
        <td>€ {amount_str}</td>
        <td>
          <ac:link>
            <ri:attachment ri:filename="{file_name}" />
            <ac:plain-text-link-body><![CDATA[Download]]></ac:plain-text-link-body>
          </ac:link>
        </td>
        <td>{w_notes}</td>
        </tr>
        """,
            "html.parser",
        )
        tbody = soup.find_all("tbody")[0]
        tbody.insert(0, row)
        confluence.update_page(page_id, page_title, str(soup))
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        confluence.attach_file(new_pdf_path, "application/pdf", page_id)
