# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
import os
import smtplib
import traceback
from typing import List, Optional


class SMTP:
    """
    SMTP server with a TLS connection over port 587.
    """

    host: str
    port: int
    user: str
    password: str
    default_from_address: str
    html_signature: str

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        default_from_address: str,
        html_signature: str,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.default_from_address = default_from_address
        self.html_signature = html_signature

    def send_mime_multipart(
        self,
        to: List[str],
        subject: str,
        body_html: str,
        from_address: Optional[str] = None,
        cc: List[str] = [],
        attachments: List[str] = [],
        images: List[str] = [],
    ):
        outer = MIMEMultipart("related")
        outer["Subject"] = subject
        outer["From"] = from_address or self.default_from_address
        outer["To"] = ", ".join(to)
        outer["X-Mailer"] = "Photocopieuse"
        outer.preamble = (
            "If you see this, please open this message with a MIME-aware mail reader.\n"
        )
        html = f"""<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=iso-8859-15">
  </head>
  <body bgcolor="#FFFFFF" text="#000000">
    {body_html}
    <br>
    <div class="moz-signature">-- <br>
      {self.html_signature}
    </div>
  </body>
</html>"""
        outer.attach(MIMEText(html, "html"))
        for att in attachments:
            try:
                with open(att, "rb") as fp:
                    msg = MIMEBase("application", "octet-stream")
                    msg.set_payload(fp.read())
                encoders.encode_base64(msg)
                msg.add_header(
                    "Content-Disposition", "attachment", filename=os.path.basename(att)
                )
                outer.attach(msg)
            except Exception:
                logging.error(
                    "Unable to open one of the attachments. " + traceback.format_exc()
                )
                return
        # Add images, maily used for signatures
        for image_filename in images:
            with open(image_filename, "rb") as image:
                msg = MIMEImage(image.read())
            image_title = os.path.splitext(os.path.basename(image_filename))[0]
            msg.add_header("Content-ID", f"<{image_title}>")
            outer.attach(msg)
        composed = outer.as_string()
        # Send the email
        with smtplib.SMTP(self.host, self.port) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(self.user, self.password)
            all_tos = to
            if cc:
                all_tos += cc
            s.sendmail(outer["From"], all_tos, composed)
            s.close()
        logging.debug("Email sent!")
