# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict

from secretary import Renderer


class Templating:
    """
    Pseudo-server to merge data into ODT templates and,
    if LibreOffice is installed and found to convert them into PDF files.
    """

    def get_soffice(self):
        soffice = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if not os.path.exists(soffice):
            soffice = "soffice"
        return soffice

    def render_template(
        self, template_file: str, rendered_file: str, values: Dict[str, Any], pdf: bool
    ):
        logging.info(
            f"Rendering template {template_file} into {rendered_file} (PDF = {pdf})..."
        )
        engine = Renderer()
        result = engine.render(template_file, **values)
        with open(rendered_file, "wb") as outf:
            outf.write(result)
        if pdf:
            soffice = self.get_soffice()
            saved_dir = os.getcwd()
            os.chdir(os.path.dirname(rendered_file))
            cmd = f"{soffice} --headless --convert-to pdf '{os.path.basename(rendered_file)}'"
            out = subprocess.run([soffice, "--headless", "--convert-to", "pdf", os.path.basename(rendered_file)])
            os.chdir(saved_dir)
            os.unlink(rendered_file)
