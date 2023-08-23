# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale
from datetime import datetime
import locale
import re
import shutil
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
        gross: float,
        net: float,
        pdf: str,
        notes: str
    ):
        params = cast(Dict[str, str], self.helper["parameters"])
        with different_locale("it_IT"):  # type: ignore
            day_str = day.strftime("%Y-%m").lower()
            file_name = day.strftime("%Y_%m")
            if notes:
                file_name += "_" + re.sub(r"\W", "_", notes.lower())
            file_name += ".pdf"
            #
            # Upload the attachment to the local DokuWiki copy
            #
            wiki_file_name = dirjoin(params["paycheck_dir"], file_name)
            shutil.copyfile(pdf, wiki_file_name)
        #
        # Update the specific bill wiki page
        #
            with change_locale("de_DE"):
                gross_str = locale.format_string("%.2f", gross)
                net_str = locale.format_string("%.2f", net)
            with open(params["paycheck_file"], encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines()]
            print(lines)
            index = lines.index(params["paycheck_heading"])
            if notes:
                day_str = f"{day_str} ({notes})"
            newline = f"|{day_str}|€ {gross_str}|€ {net_str}| {{{{ {params['paycheck_prefix'] + file_name}'?linkonly|Download}}}} |"
            lines.insert(index + 1, newline)
            with open(params["paycheck_file"], "w", encoding="utf-8") as f:
                f.write("\n".join(lines))