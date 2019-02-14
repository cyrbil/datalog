#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import curses

import humanize

from datalog_http_monitoring import cli_swag_tpl as tpl
from datalog_http_monitoring.http_logs_stats import HTTPLogsStats


def n_fmt(n: float, precision: int = 1):
    """
    Format a number to a short string representation.

    :param n: a number
    :type n: float
    :param precision: number of decimal to display
    :type precision: int
    :return: a 4 + `precision` length string
    """
    for unit in [None, 'k', 'M', 'B']:
        if abs(n * (10 if unit else 1)) < 1000.0:
            if not unit:
                return str(n)
            return f"{n:3.{precision}f}{unit}"
        n /= 1000.0
    return f"{n:.{precision}f}T"


class CliSwag(object):
    def __init__(self, refresh_time: int = 1, use_curses: bool = True):
        """
        A CLI with nice color and border and stuff...

        It has 3 modes:
          - Curses with color (default), fastest and nicest UI
          - Curses without color (default on incompatible terminals), fastest and ugliest UI
          - Print with color, slowest with flickering

        Displayed template is in `cli_swag_tpl.py`, have a look there to comprehend colors and stuff.

        :param refresh_time: delay between each screen refresh
        :type refresh_time: int
        :param use_curses: option to enable/disable curses display
        :type use_curses: bool
        """
        self.refresh_time = refresh_time
        self.next_refresh = None

        # curse main window
        self.stdscr = None
        if use_curses:
            # Initialize curses
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(1)
            try:
                curses.curs_set(0)
            except curses.error:
                pass

            try:
                curses.start_color()
                curses.use_default_colors()
                for i, color in enumerate(tpl.COLORS):
                    curses.init_pair(i, color, -1)
            except curses.error:
                # notice that most curses error for initscr are not catchable
                pass

            # this pad will contain the UI
            self.scr_pad = curses.newpad(100, 100)

            # noinspection PyUnresolvedReferences
            self.borders_map = {
                '│': curses.ACS_VLINE,
                '─': curses.ACS_HLINE,
                '┌': curses.ACS_ULCORNER,
                '┐': curses.ACS_URCORNER,
                '┘': curses.ACS_LRCORNER,
                '└': curses.ACS_LLCORNER,
                '┬': curses.ACS_TTEE,
                '┤': curses.ACS_RTEE,
                '┴': curses.ACS_BTEE,
                '├': curses.ACS_LTEE,
            }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def shutdown(self):
        """
        Must be called for curses to exit properly
        """
        if self.stdscr:
            self.stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    def update(self, http_stats: HTTPLogsStats):
        """
        Receive a `HTTPLogsStats` instance to display and show it

        :param http_stats: a `HTTPLogsStats` instance
        :type http_stats: HTTPLogsStats
        """

        now = time.time()
        # do not refresh before next_refresh
        if self.next_refresh and self.next_refresh > now:
            return

        self.next_refresh = now + self.refresh_time
        content = self.format_stats(http_stats)
        self._display(content)

    def _display(self, content: str):
        if self.stdscr:
            self._display_curses(content)
        else:
            self._display_print(content)

    def _display_curses(self, content: str):
        self.scr_pad.erase()

        for char in content:
            char_idx = ord(char)
            if char_idx < 9:  # its a color reference character
                # noinspection PyUnresolvedReferences
                if curses.has_colors() and curses.COLORS == 256:
                    self.scr_pad.attrset(curses.color_pair(char_idx))
            elif char in self.borders_map:
                self.scr_pad.addch(self.borders_map[char])
            else:
                self.scr_pad.addch(char)

        # noinspection PyUnresolvedReferences
        self.scr_pad.refresh(0, 0, 0, 0, curses.LINES - 1, curses.COLS - 1)

    @staticmethod
    def _display_print(content: str):
        if os.name == 'nt':
            os.system('cls')
        else:
            print("\033c")

        content_colored_ansi = content
        for char_idx, color in enumerate(tpl.COLORS):
            content_colored_ansi = content_colored_ansi.replace(chr(char_idx), f"\x1b[38;5;{color:d}m")
        print(content_colored_ansi)

    def format_stats(self, http_stats: HTTPLogsStats) -> str:
        """
        Format a `HTTPLogsStats` instance into `template`

        :param http_stats: a `HTTPLogsStats` instance
        :type http_stats: HTTPLogsStats
        :return: formatted template
        """
        # transform to dict
        data = self.get_data(http_stats)

        # template contains lines with different purpose, this parts use them according to http_stats
        tpl_lines = tpl.TEMPLATE.splitlines()

        # tpl_arr will contain all lines to display, starting with the header
        tpl_arr = tpl_lines[:tpl.TPL_LINE_HEADER_END]

        # then the periodic details
        detail_empty = tpl_lines[tpl.TPL_LINE_DETAIL_EMPTY]
        len_details = len(data["period_details"])
        if len_details:
            tpl_part = [tpl_lines[tpl.TPL_LINE_DETAIL_HEADER]]
            for detail in data["period_details"]:
                detail_fmt = tpl_lines[tpl.TPL_LINE_DETAIL].format(**detail)
                tpl_part.append(detail_fmt)
            if len_details < tpl.TPL_DETAILS_LEN:
                tpl_part.extend([detail_empty] * (tpl.TPL_DETAILS_LEN - len_details))
            tpl_part.extend(tpl_lines[tpl.TPL_LINE_DETAILS_STATS_START:tpl.TPL_LINE_DETAILS_STATS_END])
        else:
            tpl_part = [detail_empty, tpl_lines[tpl.TPL_LINE_DETAILS_NONE]] \
                     + ([detail_empty] * (tpl.TPL_DETAILS_LEN + 2))

        tpl_arr.extend(tpl_part)
        tpl_arr.extend(tpl_lines[tpl.TPL_LINE_DETAILS_STATS_END:tpl.TPL_LINE_DETAILS_END])

        # finally the alerting details
        alert_empty = tpl_lines[tpl.TPL_LINE_ALERT_EMPTY]
        len_alerts = len(data["alerts"])
        if len_alerts:
            alert_line_ok = tpl_lines[tpl.TPL_LINE_ALERT_OK]
            alert_line_ko = tpl_lines[tpl.TPL_LINE_ALERT_KO]
            tpl_part = []
            for alert in data["alerts"]:
                if alert.get("alert_finished"):
                    alert_fmt = alert_line_ok.format(**alert)
                    tpl_part.append(alert_fmt)
                alert_fmt = alert_line_ko.format(**alert)
                tpl_part.append(alert_fmt)
            if len_alerts < tpl.TPL_ALERT_LEN:
                tpl_part.extend([alert_empty] * (1 + tpl.TPL_ALERT_LEN - len(tpl_part)))
        else:
            tpl_part = [alert_empty, tpl_lines[tpl.TPL_LINE_ALERT_NONE]] + ([alert_empty] * (tpl.TPL_ALERT_LEN - 1))

        tpl_arr.extend(tpl_part[:1 + tpl.TPL_ALERT_LEN])

        # and the footer
        tpl_arr.extend(tpl_lines[tpl.TPL_LINE_ALERT_END:])

        # join everything in a string to apply formatting and remove spacers
        template = os.linesep.join(p.strip('\n') for p in tpl_arr)
        content = template.format(**data)
        content = content.replace("'", '')
        return content

    @staticmethod
    def get_data(http_stats: HTTPLogsStats) -> dict:
        """
        Transform a `HTTPLogsStats` instance to dict with formatted values
        :param http_stats: a `HTTPLogsStats` instance
        :type http_stats: HTTPLogsStats
        :return: dict
        """
        data = {
            "config_period": f"{humanize.naturaldelta(http_stats.period)} \1",

            "total_requests": n_fmt(http_stats.all_stats.hits, 2),
            "total_valid": n_fmt(http_stats.all_stats.valid_requests, 2),
            "total_fail": n_fmt(http_stats.all_stats.hits - http_stats.all_stats.valid_requests, 2),
            "total_visitors": n_fmt(len(http_stats.all_stats.visitors), 2),
            "total_files": n_fmt(len(http_stats.all_stats.paths), 2),
            "total_bandwidth": humanize.naturalsize(http_stats.all_stats.bandwidth),

            "total_200": n_fmt(http_stats.all_stats.status_codes.get("200", 0)),
            "total_404": n_fmt(http_stats.all_stats.status_codes.get("404", 0)),
            "total_2XX": n_fmt(http_stats.all_stats.status_codes.get("2XX", 0)),
            "total_3XX": n_fmt(http_stats.all_stats.status_codes.get("3XX", 0)),
            "total_4XX": n_fmt(http_stats.all_stats.status_codes.get("4XX", 0)),
            "total_5XX": n_fmt(http_stats.all_stats.status_codes.get("5XX", 0)),

            "alert_status": "\2OK" if not http_stats.in_alert else "\10KO",
            "log_file": "/tmp/access.log",  # todo: display real file name ...

            "period_details": CliSwag._get_period_details(http_stats),

            "period_date": f"{http_stats.period_start:%d/%m/%y}",
            "period_time": f"{http_stats.period_start:%H:%M:%S}",
            "period_requests": http_stats.period_stats.hits,
            "period_visitors": len(http_stats.period_stats.visitors),
            "period_files": len(http_stats.period_stats.paths),
            "period_reqs_rate": n_fmt(http_stats.period_stats.hits / http_stats.period),
            "period_bandwidth": humanize.naturalsize(http_stats.period_stats.bandwidth),

            "period_200": http_stats.period_stats.status_codes.get("200", 0),
            "period_404": http_stats.period_stats.status_codes.get("404", 0),
            "period_2XX": http_stats.period_stats.status_codes.get("2XX", 0),
            "period_3XX": http_stats.period_stats.status_codes.get("3XX", 0),
            "period_4XX": http_stats.period_stats.status_codes.get("4XX", 0),
            "period_5XX": http_stats.period_stats.status_codes.get("5XX", 0),

            "alert_log": "/tmp/alerts.log",
            "alert_threshold": "(>{} reqs/s on average over {}) \1".format(
                http_stats.alert_rate_threshold,
                humanize.naturaldelta(http_stats.alert_period)
            ),
            "alerts": CliSwag._get_data_alerts(http_stats)
        }

        return data

    @staticmethod
    def _get_period_details(http_stats: HTTPLogsStats):
        period_details = []

        top_sections = http_stats.period_stats.sections.most_common()
        top_5_sections = top_sections[0:5]

        for section_name, _ in top_5_sections:
            section = http_stats.period_stats.sections_stats[section_name]
            section_stats = {
                "detail_hits": section.hits,
                "detail_hits_r": 0,
                "detail_visitors": len(section.visitors),
                "detail_visitors_r": 0,
                "detail_bandwidth": section.bandwidth,
                "detail_subsections": len(section.paths),
                "detail_path": f"/{section_name}"
            }
            period_details.append(section_stats)

        others_sections = top_sections[5:]
        if others_sections:
            other_sections_cumulated = {
                "detail_hits": 0,
                "detail_hits_r": 0,
                "detail_visitors": 0,
                "detail_visitors_r": 0,
                "detail_bandwidth": 0,
                "detail_subsections": 0,
                "detail_path": f"({len(others_sections)} others)"
            }

            for section_name, _ in others_sections:
                section = http_stats.period_stats.sections_stats[section_name]
                other_sections_cumulated["detail_hits"] += section.hits
                other_sections_cumulated["detail_visitors"] += len(section.visitors)
                other_sections_cumulated["detail_bandwidth"] += section.bandwidth
                other_sections_cumulated["detail_subsections"] += len(section.paths)

            period_details.append(other_sections_cumulated)

        for detail in period_details:
            detail["detail_hits_r"] = detail["detail_hits"] / http_stats.period_stats.hits
            detail["detail_visitors_r"] = detail["detail_visitors"] / len(http_stats.period_stats.visitors)
            detail["detail_bandwidth"] = humanize.naturalsize(detail["detail_bandwidth"])

        return period_details

    @staticmethod
    def _get_data_alerts(http_stats: HTTPLogsStats):
        alerts = []
        for i in range(0, min(4, len(http_stats.alerts))):
            alert = http_stats.alerts[-(i + 1)]
            alert_detail = {
                "alert_hits": n_fmt(len(alert.logs)),
                "alert_start": f"{alert.start:%d/%m/%y, %H:%M:%S}",
                "alert_end": f"{alert.end:%d/%m/%y, %H:%M:%S}",
                "alert_finished": alert.finished,
                "alert_duration": humanize.naturaldelta(alert.duration)
            }

            alerts.append(alert_detail)

        return alerts
