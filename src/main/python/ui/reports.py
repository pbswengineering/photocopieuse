# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime, timedelta
import logging
import os
import traceback
from typing import cast, Dict, Optional

from PyQt5 import QtCore, uic
from PyQt5.Qt import QMessageBox
from PyQt5.QtWidgets import (
    QDateEdit,
    QPushButton,
    QWidget,
    QApplication,
)

from config import HelperType
from organization import Organization
from service.excelreports import ReportType, ExcelReports
from service.timetracker import Timetracker
from ui.abstractcontext import AbstractContext
from ui.abstractui import AbstractUI
from ui.basetask import BaseTask

from utils import change_locale


class ReportsUI(AbstractUI):

    organization: Organization
    _widget: Optional[QWidget]
    pb_close: QPushButton
    pb_edit_forecast: QPushButton
    pb_send_forecast: QPushButton
    pb_edit_final: QPushButton
    pb_send_final: QPushButton
    pb_edit_monthly: QPushButton
    pb_send_monthly: QPushButton
    pb_timetracker: QPushButton
    pb_worklog: QPushButton
    de_worklog: QDateEdit
    signal_success = QtCore.pyqtSignal()
    signal_failure = QtCore.pyqtSignal(str)
    excel_reports: ExcelReports

    def __init__(
        self,
        context: AbstractContext,
        organization: Organization,
        helper: HelperType,
        qapp: QApplication,
    ):
        super().__init__(qapp, context)
        self.context = context
        self.organization = organization
        self.helper = helper
        self._widget = None
        self.excel_reports = ExcelReports(organization, helper)

    def widget(self) -> QWidget:
        if not self._widget:
            self._widget = uic.loadUi(self.context.get_resource("ui/reports.ui"))
            self.pb_close = self._widget.findChild(QPushButton, "pbClose")
            self.pb_close.clicked.connect(self.pb_close_clicked)
            self.pb_edit_forecast = self._widget.findChild(
                QPushButton, "pbEditForecast"
            )
            self.pb_edit_forecast.clicked.connect(self.pb_edit_forecast_clicked)
            self.pb_send_forecast = self._widget.findChild(
                QPushButton, "pbSendForecast"
            )
            self.pb_send_forecast.clicked.connect(self.pb_send_forecast_clicked)
            self.pb_edit_final = self._widget.findChild(QPushButton, "pbEditFinal")
            self.pb_edit_final.clicked.connect(self.pb_edit_final_clicked)
            self.pb_send_final = self._widget.findChild(QPushButton, "pbSendFinal")
            self.pb_send_final.clicked.connect(self.pb_send_final_clicked)
            self.pb_edit_monthly = self._widget.findChild(QPushButton, "pbEditMonthly")
            self.pb_edit_monthly.clicked.connect(self.pb_edit_monthly_clicked)
            self.pb_send_monthly = self._widget.findChild(QPushButton, "pbSendMonthly")
            self.pb_send_monthly.clicked.connect(self.pb_send_monthly_clicked)
            self.pb_timetracker = self._widget.findChild(QPushButton, "pbTimetracker")
            self.pb_timetracker.clicked.connect(self.pb_timetracker_clicked)
            self.pb_worklog = self._widget.findChild(QPushButton, "pbWorklog")
            self.pb_worklog.clicked.connect(self.pb_worklog_clicked)
            self.de_worklog = self._widget.findChild(QDateEdit, "deWorklog")
            self.de_worklog.setDateTime(datetime.now())
            self.signal_failure.connect(self.failure)
            self.signal_success.connect(self.success)
        return self._widget

    def active(self, state):
        self.pb_close.setEnabled(state)
        self.pb_edit_forecast.setEnabled(state)
        self.pb_send_forecast.setEnabled(state)
        self.pb_edit_final.setEnabled(state)
        self.pb_send_final.setEnabled(state)
        self.pb_edit_monthly.setEnabled(state)
        self.pb_send_monthly.setEnabled(state)
        self.pb_timetracker.setEnabled(state)
        self.pb_worklog.setEnabled(state)
        self.de_worklog.setEnabled(state)

    def failure(self, message: str):
        self.message_error(f"Unable to write Jira worklog. \n{message}")
        self.context.clear_status()
        self.active(True)
        self.pb_close_clicked()

    def success(self):
        self.message_info("Worklog insertion completed.")
        self.context.clear_status()
        self.active(True)
        self.pb_close_clicked()

    def xdg_open(self, file):
        os.system(f"xdg-open '{file}'")

    def open_excel(self, report_type: ReportType):
        file = self.excel_reports.get_today_file(report_type, datetime.now())
        logging.debug(f"Opening {file}")
        if not file or not os.path.exists(file):
            self.message_error(
                "Report file not found (check your configuration and make sure that the template is available)"
            )
        if file and os.path.exists(file):
            self.xdg_open(file)
        self.pb_close_clicked()

    def get_images(self):
        params = cast(Dict[str, str], self.helper["parameters"])
        images = params["images"].split(",")
        base_dir = params["images_dir"].replace("${HOME}", os.environ["HOME"])
        return [os.path.join(base_dir, f"{f}.jpg") for f in images]

    def send_report(self, report_type: ReportType, now: datetime = None):
        params = cast(Dict[str, str], self.helper["parameters"])
        self.active(False)
        if not now:
            now = datetime.now()
        file = self.excel_reports.get_today_file(report_type, now)
        logging.debug(f"Opening {file}")
        if not file or not os.path.exists(file):
            self.message_error("Report file not found")
            return
        with change_locale("it_IT.utf8"):
            if report_type == ReportType.forecast:
                subject = "Preventivo " + now.strftime("%d/%m/%Y")
                body = (
                    f"<p>Allego il preventivo di oggi.</p><p>{params['signature']}</p>"
                )
            elif report_type == ReportType.final:
                subject = "Consuntivo " + now.strftime("%d/%m/%Y")
                body = (
                    f"<p>Allego il consuntivo di oggi.</p><p>{params['signature']}</p>"
                )
            elif report_type == ReportType.monthly:
                subject = "Presenze " + now.strftime("%B %Y")
                month_str = now.strftime("%B %Y")
                body = f"<p>Allego le presenze per il mese di {month_str}.</p><p>{params['signature']}<br>"
        smtp = self.organization.smtp()
        try:
            if report_type == ReportType.monthly:
                to_emails = params["rcpt_to_daily"].split(",")
            else:
                to_emails = params["rcpt_to_monthly"].split(",")
            smtp.send_mime_multipart(
                to_emails,
                subject,
                body,
                params["from_address"],
                params["rcpt_cc_daily"].split(","),
                [file],
                self.get_images(),
            )
            if report_type == ReportType.forecast:
                self.message_info(
                    "The daily forecast report email has been sent correctly."
                )
            elif report_type == ReportType.final:
                self.message_info(
                    "The daily final report email has been sent correctly."
                )
            elif report_type == ReportType.monthly:
                self.message_info("The monthly report email has been sent correctly.")
        except Exception:
            self.message_error("Unable to send the email. " + traceback.format_exc())
        finally:
            self.active(True)
            self.pb_close_clicked()

    def pb_edit_forecast_clicked(self):
        self.open_excel(ReportType.forecast)

    def pb_send_forecast_clicked(self):
        # First, check if it's the appropriate time of the day to send the report
        now = datetime.now()
        if now.hour >= 10 and not self.message_yes_no(
            "It's past 10 am, are you sure you want to send the FORECAST report email?"
        ):
            return
        self.send_report(ReportType.forecast)

    def pb_edit_final_clicked(self):
        self.open_excel(ReportType.final)

    def pb_send_final_clicked(self):
        # First, check if it's the appropriate time of the day to send the report
        now = datetime.now()
        if now.hour < 18 and not self.message_yes_no(
            "It's before 6 pm, are you sure you want to send the FINAL report email?"
        ):
            return
        self.send_report(ReportType.final)

    def pb_edit_monthly_clicked(self):
        self.open_excel(ReportType.monthly)

    def message_yes_no_cancel(self, question: str, yes: str, no: str) -> int:
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Photocopieuse")
        box.setText(question)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        btYes = box.button(QMessageBox.Yes)
        btYes.setText(yes)
        btNo = box.button(QMessageBox.No)
        btNo.setText(no)
        return box.exec_()

    def pb_send_monthly_clicked(self):
        if not self.message_yes_no(
            "Are you sure you want to send the MONTHLY report email?"
        ):
            return
        now = datetime.now()
        # I often send the monthly report in the first days
        # of the subsequent month
        if now.day < 20:
            before = now - timedelta(days=25)  # It works on Mar/Feb too
            curr_month = now.strftime("%B")
            prev_month = before.strftime("%B")
            choice = self.message_yes_no_cancel(
                f"Would you like to send the report for the month of {curr_month}?",
                f"Yes, send the {curr_month} report",
                f"No, send the {prev_month} report",
            )
            if choice == QMessageBox.Cancel:
                return
            elif choice == QMessageBox.No:
                now = before
        self.send_report(ReportType.monthly, now)

    def pb_timetracker_clicked(self):
        self.xdg_open(self.helper["parameters"]["timetracker_url"])
        self.pb_close_clicked()

    def pb_worklog_clicked(self):
        self.active(False)
        worklog_date = self.de_worklog.dateTime().toPyDateTime()
        self.context.show_status("Uploading worklogs...")
        WorklogTask(self, worklog_date).start()


class WorklogTask(BaseTask):
    ui: ReportsUI
    worklog_date: datetime

    def __init__(self, ui: ReportsUI, worklog_date: datetime):
        super().__init__()
        self.ui = ui
        self.worklog_date = worklog_date

    def run(self):
        try:
            params = self.ui.helper["parameters"]
            sending_time = self.ui.excel_reports.get_sending_time(self.worklog_date)
            worklogs = self.ui.excel_reports.parse_worklogs(
                self.worklog_date, sending_time, params["worklog_jira_user"]
            )
            jira = self.ui.organization.jira()
            registre_de_travail = Timetracker(self.ui.organization, self.ui.helper)
            worklogs_to_delete = registre_de_travail.get_worklogs(
                self.worklog_date, users=[params["jira_user"]]
            )
            for worklog_to_delete in worklogs_to_delete[params["jira_user"]]:
                jira.delete_worklog(worklog_to_delete)
            for worklog in worklogs:
                jira.add_worklog(worklog)
            self.ui.signal_success.emit()
        except Exception:
            self.ui.signal_failure.emit(traceback.format_exc())
