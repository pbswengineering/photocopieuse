# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime
import locale as _locale
import os
import subprocess
from tempfile import mktemp
from typing import List

from PyQt5.QtCore import QLocale


def set_utf8_locale(category: int, locname: str):
    try:
        _locale.setlocale(category, locname)
    except _locale.Error as ex:
        if locname.endswith(".utf8"):
            _locale.setlocale(
                category, locname[: len(locname) - len(".utf8")] + ".UTF-8"
            )
        else:
            raise ex


def set_default_locale():
    set_utf8_locale(_locale.LC_ALL, "en_GB.utf8")
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))


class change_locale:
    def __init__(self, locale):
        self.locale = locale

    def __enter__(self):
        self.oldlocale = _locale.getlocale(_locale.LC_TIME)
        set_utf8_locale(_locale.LC_ALL, self.locale)

    def __exit__(self, *args):
        try:
            _locale.setlocale(_locale.LC_ALL, self.oldlocale)
        except _locale.Error:
            pass


def concatenate_pdfs(pdf_files: List[str]) -> str:
    out_pdf = mktemp(".pdf")
    subprocess.check_call(
        ["pdftk"] + pdf_files + ["cat", "output", out_pdf], universal_newlines=True
    )
    return out_pdf


def replace_path_vars(path: str) -> str:
    return path.replace("${HOME}", os.path.expanduser("~"))


ITA_WEEKDAYS = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
    "sabato",
    "domenica",
]


def ita_weekday(d: datetime) -> str:
    return ITA_WEEKDAYS[d.weekday()]
