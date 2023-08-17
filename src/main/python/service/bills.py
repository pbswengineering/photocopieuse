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
import shutil
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
            month_str = t_month.strftime("%Y_%m")
            month_str_for_table = t_month.strftime("%B %Y").lower()
            file_name = f"bolletta_{month_str}.pdf"
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        wiki_file_name = dirjoin(params["telephone_dir"], file_name)
        shutil.copyfile(new_pdf_path, wiki_file_name)
        #
        # Update the specific bill wiki page
        #
        due_date_str = t_due_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", t_amount)
        with open(params["telephone_file"]) as f:
            lines = f.readlines()
        index = lines.index(params["telephone_heading"])
        newline = f"|{due_date_str}|{month_str_for_table}|€ {amount_str}| {{{{ {params['telephone_prefix'] + file_name}'?linkonly|Download}}}} | {t_notes} |\n"
        lines.insert(index + 1, newline)
        with open(params["telephone_file"], "w") as f:
            f.writelines(lines)

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
            month_str = e_due_date.strftime("%Y_%m")
            file_name = f"bolletta_{month_str}.pdf"
        #
        # Upload the attachment to the local DokuWiki copy
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        wiki_file_name = dirjoin(params["electricity_dir"], file_name)
        shutil.copyfile(new_pdf_path, wiki_file_name)
        #
        # Update the specific bill wiki page
        #
        due_date_str = e_due_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", e_amount)
        with open(params["electricity_file"]) as f:
            lines = f.readlines()
        index = lines.index(params["electricity_heading"])
        newline = f"|{due_date_str}|{e_interval}|€ {amount_str}| {{{{ {params['electricity_prefix'] + file_name}'?linkonly|Download}}}} | {e_notes} |\n"
        lines.insert(index + 1, newline)
        with open(params["electricity_file"], "w") as f:
            f.writelines(lines)

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
            month_str = g_date.strftime("%Y_%m")
            file_name = f"bolletta_gas_{month_str}.pdf"
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        wiki_file_name = dirjoin(params["gas_dir"], file_name)
        shutil.copyfile(new_pdf_path, wiki_file_name)
        #
        # Update the specific bill wiki page
        #
        date_str = g_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", g_amount)
        with open(params["gas_file"]) as f:
            lines = f.readlines()
        index = lines.index(params["electricity_heading"])
        newline = f"|{date_str}|{g_interval}|€ {amount_str}|{g_cubic_meters}|{{{{ {params['gas_prefix'] + file_name}'?linkonly|Download}}}} | {g_notes} |\n"
        lines.insert(index + 1, newline)
        with open(params["gas_file"], "w") as f:
            f.writelines(lines)

    def upload_water(
        self,
        w_date: datetime,
        w_interval: str,
        w_amount: float,
        w_house: str,
        w_notes: str,
        pdf_files: List[str],
    ):
        params = cast(Dict[str, str], {x: y.replace("[house]", w_house) for x, y in self.helper["parameters"].items()})
        with different_locale("it_IT"):  # type: ignore
            month_str = w_date.strftime("%Y_%m")
            file_name = f"bolletta_acqua_{month_str}.pdf"
        #
        # Upload the attachment to Phabricator
        #
        if len(pdf_files) > 1:
            pdf_file = concatenate_pdfs(pdf_files)
        else:
            pdf_file = pdf_files[0]
        new_pdf_path = os.path.join(os.path.dirname(pdf_file), file_name)
        os.rename(pdf_file, new_pdf_path)
        wiki_file_name = dirjoin(params["water_dir"], file_name)
        shutil.copyfile(new_pdf_path, wiki_file_name)
        #
        # Update the specific bill wiki page
        #
        date_str = w_date.strftime("%d/%m/%Y")
        with change_locale("de_DE"):
            amount_str = locale.format_string("%.2f", w_amount)
        with open(params["water_file"]) as f:
            lines = f.readlines()
        index = lines.index(params["water_heading"])
        newline = f"|{date_str}|{w_interval}|€ {amount_str}|{{{{ {params['water_prefix'] + file_name}?linkonly|Download}}}}|{w_notes}|\n"
        lines.insert(index + 1, newline)
        with open(params["water_file"], "w") as f:
            f.writelines(lines)
