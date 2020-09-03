# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import date, datetime, timedelta
import logging
import os
from typing import Dict, List, Optional

import requests
from requests.models import Response


class Record:
    """
    A single check-in/check-out record. Check-in and check-out can be None
    and the check-out can be set automatically by BadgeBox.
    """

    checkin: Optional[datetime]
    checkout: Optional[datetime]
    auto_checkout: bool

    def __init__(
        self,
        checkin: Optional[datetime] = None,
        checkout: Optional[datetime] = None,
        auto_checkout: bool = False,
    ):
        """
        :param checkin: optional clock-in timestamp
        :param checkout: optional clock-out timestamp
        :param auto_checkout: True if the clock-out was automatically created by BadgeBox (the user forgot to do it)
        """

        self.checkin = checkin
        self.checkout = checkout
        self.auto_checkout = auto_checkout

    def __str__(self) -> str:
        s = []
        if self.checkin:
            s.append(self.checkin.strftime("%H:%M"))
        else:
            s.append("X")
        s.append(" → ")
        if self.checkout:
            s.append(self.checkout.strftime("%H:%M"))
            if self.auto_checkout:
                s.append(" (auto)")
        else:
            s.append("--.--")
        return "".join(s)

    def __repr__(self) -> str:
        s = ["Record("]
        if self.checkin:
            s.append(self.checkin.strftime("%Y-%m-%d %H:%M"))
        else:
            s.append("X")
        s.append(" → ")
        if self.checkout:
            s.append(self.checkout.strftime("%Y-%m-%d %H:%M"))
            if self.auto_checkout:
                s.append(" (auto)")
        else:
            s.append("--.--")
        s.append(")")
        return "".join(s)

    def __lt__(self, other) -> bool:
        if not isinstance(other, Record):
            return False
        elif self.checkin and other.checkin:
            return self.checkin < other.checkin
        elif self.checkin and not other.checkin:
            return False
        elif not self.checkin and other.checkin:
            return True
        elif self.checkout and other.checkout:
            return self.checkout < other.checkout
        elif self.checkout and not other.checkout:
            return False
        elif not self.checkout and other.checkout:
            return True
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, Record):
            return (
                other.checkin == self.checkin
                and other.checkout == self.checkout
                and other.auto_checkout == self.auto_checkout
            )
        else:
            return False


class Records:
    """
    BadgeBox records grouped by date.
    """

    from_date: date
    to_date: date
    records: Dict[str, List[Record]]

    def __init__(self, from_date: date, to_date: date):
        """
        :param from_date: first date of the range (inclusive)
        :param to_date: last date of the range (inclusive)
        """

        self.from_date = from_date
        self.to_date = to_date
        self.records = {}
        d = from_date
        while d <= to_date:
            self.records[d.strftime("%Y-%m-%d")] = []
            d += timedelta(days=1)

    def __len__(self) -> int:
        """
        :return: it actually returns the number of days where there are records (a day may have more than 1 record)
        """

        return len(self.records)

    def __contains__(self, record) -> bool:
        if isinstance(record, Record):
            key = record.checkin or record.checkout
            if key:
                return record in self.records[key.strftime("%Y-%m-%d")]
        return False

    def add_record(self, record: Record):
        """
        Add a new record to the list.

        :param record: the record to add
        """

        if not record.checkin and not record.checkout:
            return
        key = record.checkin or record.checkout
        if not key:
            return
        key_str = key.date().strftime("%Y-%m-%d")
        if key_str not in self.records:
            return
        if record in self.records[key_str]:
            return
        self.records[key_str].append(record)
        self.records[key_str].sort()


class BadgeBox:
    """
    BadgeBox API wrapper.
    """

    server_url: str
    username: str
    password: str
    headers: Dict[str, str]
    session: Optional[str]
    logged_in: bool

    def __init__(self, username: str, password: str):
        self.server_url = "https://www.badgebox.com/server/version_rc4_0"
        self.username = username
        self.password = password
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        self.session = None
        self.logged_in = False

    def response_to_json(self, response: Response):
        """
        Convert a Requests response to a JSON-like dict.

        :param response: Requests response
        :return: a JSON-like object
        :raises HTTPError: non-200 HTTP statuses
        :raises Exception:
        """

        response.raise_for_status()
        json_response = response.json()
        if "ERROR" in json_response:
            # e.g. {'ERROR': {'TYPE': 0, 'MESSAGE': 'Login required', 'PAYLOAD': None}}
            raise Exception(json_response)
        return json_response

    def login(self):
        """
        Log into BadgeBox and open a new session.

        :raises HTTPError: non-200 HTTP statuses
        :raises Exception:
        """

        logging.debug("BADGEBOX API CALL: login")
        url = os.path.join(self.server_url, "user/login")
        data = {"username": self.username, "password": self.password}
        response = requests.post(url, headers=self.headers, data=data)  # type: Response
        json_response = self.response_to_json(response)
        self.session = json_response["user"]["session"]
        logging.debug(f"BADGEBOX API RETURN: login → {self.session}")
        self.logged_in = True

    def logout(self):
        """
        Log out from BadgeBox (it works even if there wasn't a previous login).

        :raises HTTPError: non-200 HTTP statuses
        :raises Exception:
        """

        logging.debug("BADGEBOX API CALL: logout")
        url = os.path.join(self.server_url, "user/logout")
        requests.post(url, headers=self.headers)
        logging.debug("BADGEBOX API RETURN: logout")

    def json_to_record(self, json_record) -> Record:
        """
        Convert a JSON BadgeBox record to a Record object.

        :param json_record: JSON-like structure containing a BadgeBox record
        :return: a Record object
        """

        if "checkin" in json_record and json_record["checkin"]:
            checkin = datetime.strptime(
                json_record["checkin"], "%Y-%m-%d %H:%M:%S"
            )  # type: Optional[datetime]
        else:
            checkin = None
        if "checkout" in json_record and json_record["checkout"]:
            checkout = datetime.strptime(
                json_record["checkout"], "%Y-%m-%d %H:%M:%S"
            )  # type: Optional[datetime]
            auto_checkout = (
                "ckout_place" in json_record and json_record["ckout_place"] == ""
            )
        else:
            checkout = None
            auto_checkout = False
        return Record(checkin, checkout, auto_checkout)

    def get_records(
        self, from_date: date, to_date: date, include_last: bool = True
    ) -> Records:
        """
        Download the presence sheet for the current month.

        :param from_date: first day of the requested record range
        :param to_date: last_day of the requested record range
        :param include_last: if True, include the last - possibly incomplete - clocking (it does a second AJAX call)
        :raises HTTPError: non-200 HTTP statuses
        :raises Exception:
        """

        self.login()
        url = os.path.join(self.server_url, "record/all")
        from_tstamp = from_date.strftime("%Y-%m-%d") + " 00:00:00"
        to_tstamp = to_date.strftime("%Y-%m-%d") + " 23:59:00"
        logging.debug(f"BADGEBOX API CALL: get_records({from_tstamp}, {to_tstamp})")
        data = {"session": self.session, "from": from_tstamp, "to": to_tstamp}
        response = requests.post(url, headers=self.headers, data=data)  # type: Response
        with open("/tmp/records.json", "w") as f:
            f.write(response.text)
        json_response = self.response_to_json(response)
        records = Records(from_date, to_date)
        for rec in json_response["records"]:
            record = self.json_to_record(rec)
            logging.debug(f"ADDING RECORD: {repr(record)}")
            records.add_record(record)
        if include_last:
            last_record = self.get_last_record()
            if last_record and (last_record.checkin or last_record.checkout):
                records.add_record(last_record)
        logging.debug(f"BADGEBOX API RETURN: get_records → {len(records)} records")
        return records

    def get_last_record(self) -> Optional[Record]:
        """
        :return: the last clocking, possibily incomplete
        """

        self.login()
        logging.debug("BADGEBOX API CALL: get_last_record")
        url = os.path.join(self.server_url, "track/lastRecord")
        data = {"session": self.session}
        response = requests.post(url, headers=self.headers, data=data)  # type: Response
        with open("/tmp/last_record.json", "w") as f:
            f.write(response.text)
        json_response = self.response_to_json(response)
        logging.debug(
            f"BADGEBOX API RETURN: get_last_record → {len(json_response)} records"
        )
        for rec in json_response["values"]:
            return self.json_to_record(rec)  # It ought to be only 1 record, anyway...
        return None
