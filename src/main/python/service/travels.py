# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from calendar import different_locale, month_name
from datetime import datetime
import os
import re
from typing import cast, Dict

from config import HelperType
from organization import Organization
from utils import dirjoin


class Travels:
    """
    Automation of the activities required to prepare a travel Wiki
    section (creation of the Wiki page and of the media directory).
    """

    org: Organization
    helper: HelperType

    def __init__(self, org: Organization, helper: HelperType):
        self.org = org
        self.helper = helper

    def sanitize_location(location: str) -> str:
        return location\
            .replace(" ", "_")\
            .replace("")
    def create(self, month: int, year: int, destination: str, description: str):
        """
        Create the wiki page and media directory for the travel.
        """
        #
        # Determine the media directory name and create it
        #
        with different_locale("it_IT"):  # type: ignore
            month_str = f"{month_name[month].capitalize()} {year}"
        page_title = f"{destination} - {month_str}"
        sanitized_destination = re.sub(r"[^a-zA-Z]", "_", destination).lower()
        dir_name = f"{sanitized_destination}_{year}_{month:02d}"
        params = cast(Dict[str, str], self.helper["parameters"])
        media_dir = dirjoin(params["travels_dir"], dir_name)
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            pass
        else:
            i = 2
            while True:
                new_dir_name = f"{dir_name}_{i}"
                media_dir = dirjoin(params["travels_dir"], new_dir_name)
                if not os.path.exists(media_dir):
                    os.makedirs(media_dir)
                    dir_name = new_dir_name
                    break
        #
        # Update the travel summary page
        #
        with open(params["travels_file"]) as f:
            lines = f.readlines()
        index = lines.index(params["travels_heading"])
        print(index)
        print(month_str)
        link = params['travels_prefix'] + dir_name
        newline = f"| [[{link}|{month_str}]] | [[{link}|{destination}]] | {description} |\n"
        lines.insert(index + 1, newline)
        with open(params["travels_file"], "w") as f:
            f.writelines(lines)
        #
        # Create the travel page
        #
        page_file = dirjoin(params["travels_page_dir"], f"{dir_name}.txt")
        with open(page_file, "w") as pf:
            pf.write(f"====== {page_title} ======\n\nTBD\n")