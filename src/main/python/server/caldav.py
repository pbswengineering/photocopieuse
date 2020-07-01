# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Paolo Bernardi.
:license: GNU AGPL version 3, see LICENSE for more details.
"""

from datetime import datetime
import uuid

import caldav


class CalDAV:
    """
    Generic CalDAV calendar. The URL must be in the following form:
    https://user:pass@hostname/caldav.php/.
    """

    caldav: caldav.DAVClient
    vcalendar_date_format: str

    def __init__(self, url: str, username: str, password: str):
        self.caldav = caldav.DAVClient(url, username=username, password=password)
        self.vcalendar_date_format = "%Y%m%dT%H%M%S"

    def filter_text(self, text: str):
        """
        Filter the characters of an event text.
        """
        return text.replace(",", "\\,")

    def add_vcal_event(self, vcal: str):
        """
        Add a VCALENDAR event to the calendar.
        """
        principal = self.caldav.principal()
        calendars = principal.calendars()
        if len(calendars) == 0:
            raise Exception("There are no calendars")
        calendar = calendars[0]
        calendar.add_event(vcal)

    def add_event(
        self,
        summary: str,
        location: str,
        beginning: datetime,
        ending: datetime,
        alarm_duration_str: str,
    ):
        """
        Add an event to the calendar by specifying summary, beginning timestamp,
        ending timestamp and alarm duration (a duration in ISO fprmat).
        """
        beginning_str = beginning.strftime(self.vcalendar_date_format)
        ending_str = ending.strftime(self.vcalendar_date_format)
        event_uuid = str(uuid.uuid4())
        vcal = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PBSE//Photocopieuse//EN
BEGIN:VTIMEZONE
TZID:Europe/Rome
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
LOCATION:{location}
SUMMARY:{summary}
DTSTART;TZID=Europe/Rome:{beginning_str}
DTEND;TZID=Europe/Rome:{ending_str}
UID:{event_uuid}
TRANSP:OPAQUE
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:{alarm_duration_str}
DESCRIPTION:{summary}
END:VALARM
END:VEVENT
END:VCALENDAR"""
        self.add_vcal_event(vcal)
