# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import argparse
from importlib import import_module
import locale
import logging
import os
import shutil
import sys


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

#
# Third party library check
#
missing = False
libraries = [
    ("jinja2", "Jinja2==2.11.3"),
    ("markupsafe", "markupsafe==2.0.1"),
    ("bs4", "beautifulsoup4"),
    ("caldav", "caldav"),
    ("fbs_runtime", "fbs"),
    ("openpyxl", "openpyxl"),
    ("pdfrw", "pdfrw"),
    ("PyQt5", "pyqt5"),
    ("PyQt5.QtWebEngineWidgets", "PyQtWebEngine"),
    ("secretary", "secretary"),
]
for lib, pip in libraries:
    try:
        import_module(lib)
    except ModuleNotFoundError:
        logging.error(f"Missing library: {lib}")
        logging.error(f"---> pip install {pip}")
        missing = True
if missing:
    sys.exit(1)

from PyQt5.QtWidgets import QApplication  # noqa: E402

from config import Config  # noqa: E402
import utils  # noqa: E402
from ui.appcontext import AppContext  # noqa: E402

# External programs check
missing = False
programs = [
    "pdftk",
]
for prog in programs:
    if not shutil.which(prog):
        logging.error(f"Missing program: {prog}")
        missing = True
if missing:
    sys.exit(1)

# Locale check
missing = False
for loc in ["de_DE", "en_US", "en_GB.utf8", "it_IT.utf8"]:
    try:
        with utils.change_locale(loc):
            pass
    except locale.Error:
        logging.error(f"Missing locale: {loc}")
        missing = True
if missing:
    sys.exit(1)


#
# Palliative fix for a QWebEngineView problem.
# (see https://bugs.launchpad.net/ubuntu/+source/qtbase-opensource-src/+bug/1761708)
#
os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_egl"

#
# Palliative fix for a Mac OS X Python crash.
# (see https://stackoverflow.com/questions/58272830/python-crashing-on-macos-10-15-beta-19a582a-with-usr-lib-libcrypto-dylib)
#
if "DYLD_LIBRARY_PATH" in os.environ:
    old_dyld_library_path = os.environ["DYLD_LIBRARY_PATH"]
else:
    old_dyld_library_path = ""
os.environ["DYLD_LIBRARY_PATH"] = "/usr/local/opt/openssl/lib"
if old_dyld_library_path:
    os.environ["DYLD_LIBRARY_PATH"] += ":" + old_dyld_library_path

if __name__ == "__main__":
    utils.set_default_locale()
    FORMAT = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"
    logging.basicConfig(format=FORMAT)
    qapp = QApplication(sys.argv)
    config = Config(qapp)
    ctx = AppContext(qapp)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", help="show logs up to the DEBUG level", action="store_true"
    )
    for helper in config.helpers():
        parser.add_argument(
            "--" + str(helper["option"]),
            help=f"run the {helper['name']} helper",
            action="store_true",
        )
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    ctx.helper_mode = False
    for helper in config.helpers():
        if getattr(args, str(helper["option"])):
            ctx.helper_mode = True
            f = ctx.helper_clicked(helper)
            f()
            break
    exit_code = ctx.run()
    sys.exit(exit_code)
