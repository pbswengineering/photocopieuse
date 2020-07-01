# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import locale as _locale
import subprocess
from tempfile import mktemp
from typing import List

from PyQt5.QtCore import QLocale


def set_default_locale():
    try:
        _locale.setlocale(_locale.LC_ALL, "en_GB.utf8")
    except _locale.Error:
        _locale.setlocale(_locale.LC_ALL, "en_GB.UTF-8")
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))


class change_locale:
    def __init__(self, locale):
        self.locale = locale

    def __enter__(self):
        self.oldlocale = _locale.getlocale(_locale.LC_TIME)
        _locale.setlocale(_locale.LC_ALL, self.locale)

    def __exit__(self, *args):
        _locale.setlocale(_locale.LC_ALL, self.oldlocale)


def concatenate_pdfs(pdf_files: List[str]) -> str:
    out_pdf = mktemp(".pdf")
    subprocess.check_call(
        ["pdftk"] + pdf_files + ["cat", "output", out_pdf], universal_newlines=True
    )
    return out_pdf
