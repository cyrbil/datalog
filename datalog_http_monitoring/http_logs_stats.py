#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

from typing import List
from collections import Counter

from datalog_http_monitoring.log_collector import Log, EmptyLog
from datalog_http_monitoring.consumers_feeder import ConsumersFeeder


class Alert(object):
    """
    An alert with corresponding logs.
    """
    def __init__(self, logs: List[Log]):
        self.logs = logs
        self.start = logs[0].date
        self.end = logs[-1].date
        self.finished = False

    def update(self, log: Log):
        assert not self.finished, "Alert has ended, create another alert"
        self.logs.append(log)
        self.end = log.date

    def recover(self, log: Log):
        self.update(log)
        self.finished = True

    @property
    def duration(self):
        return (self.end - self.start).total_seconds()


class HTTPLogsStats(ConsumersFeeder):
    def __init__(self, period: int = 10, alert_period: int = 120, alert_threshold: int = 5, alert_output: str = None):
        """
        Collect total and periodic statistics from Log instances and manage alerting.

        :param period: duration in seconds of periodic statistics
        :type period: int
        :param alert_period: duration in seconds of alert monitoring
        :type alert_period: int
        :param alert_threshold: requests per seconds limit before triggering n alert
        :type alert_threshold: int
        :param alert_output: write alerts to this path
        :type alert_output: str
        """
        super(HTTPLogsStats, self).__init__()
        self.all_stats = HTTPStats()

        self.period = period
        self.period_start = None
        self.period_stats = HTTPStatsSections()
        self._period_stats = HTTPStatsSections()  # used for period stats rotations

        self.alerts = []
        self.in_alert = False
        self.alert_period = alert_period
        self.alert_rate_threshold = alert_threshold
        self.alert_rate_threshold_margin = alert_threshold / 10
        self.alert_period_logs = []

        self.alert_output = alert_output
        if alert_output:
            # ensure alert output file is writable
            with open(alert_output, "a+", encoding="utf-8"):
                pass

    def update(self, log: Log):
        """
        Collect `Log` metrics and add it to existing statistics
        :param log: a `Log` instance
        :type log: Log
        """
        if not isinstance(log, EmptyLog):
            self.all_stats.update(log)
            self._period_stats.update(log)
            self._check_alert(log)

        self._rotate_period_stats(log.date)
        self.feed_consumers(self)

    def _rotate_period_stats(self, date: datetime.datetime):
        """
        Rotate period statistics when period has ended
        :param date: current date
        :type date: datetime.datetime
        """
        if not self.period_start:
            self.period_start = date
        elif (date - self.period_start).total_seconds() >= self.period:
            self.period_stats = self._period_stats
            self._period_stats = HTTPStatsSections()
            self.period_start = date

    def _check_alert(self, log: Log):
        """
        Collect all logs during last `alert_period` seconds
        and create an alert when the requests rate get greater than `alert_rate_threshold`.

        Alert is recovered when requests rate goes under (`alert_rate_threshold` - `alert_rate_threshold_margin`)
        to avoid triggering many alerts when requests rate is just around the `alert_rate_threshold`.
        :param log: a `Log` instance
        :type log: Log
        """

        self.alert_period_logs.append(log)
        # while first and last log time diff is more than alert period
        while (self.alert_period_logs[-1].date - self.alert_period_logs[0].date).total_seconds() >= self.alert_period:
            # remove oldest log
            self.alert_period_logs.pop(0)

        # compute current requests rate
        alert_period_requests = len(self.alert_period_logs)
        alert_requests_rate = alert_period_requests / self.alert_period

        # trigger or recover alerts
        if self.in_alert:
            alert = self.alerts[-1]  # current alert
            if alert_requests_rate <= (self.alert_rate_threshold - self.alert_rate_threshold_margin):
                alert.recover(log)
                self.in_alert = False
                self.write_alert(alert)
            else:
                alert.update(log)
        else:
            if alert_requests_rate > self.alert_rate_threshold:
                alert = Alert(list(self.alert_period_logs))
                self.alerts.append(alert)
                self.in_alert = True
                self.write_alert(alert)

    def write_alert(self, alert: Alert):
        if not self.alert_output:  # pragma: no cover
            return

        if alert.finished:
            text = f"High traffic recovered at {alert.end:%d/%m/%y, %H:%M:%S} - duration:\7 {alert.duration}\n"
        else:
            text = f"High traffic generated an alert - " \
                   f"hits = {len(alert.logs)}, triggered at {alert.start:%d/%m/%y, %H:%M:%S}\n"

        with open(self.alert_output, "a", encoding="utf-8") as fd:
            fd.write(text)


class HTTPStats(object):
    """
    Collect statistics from Log instances.
    """

    def __init__(self):
        self.hits = 0
        self.visitors = Counter()
        self.valid_requests = 0
        self.status_codes = Counter()
        self.paths = Counter()
        self.sections = Counter()
        self.methods = Counter()
        self.bandwidth = 0

    def reset(self):
        self.__init__()

    def update(self, log: Log):
        """
        Collect `Log` metrics and add it to existing statistics
        :param log: a `Log` instance
        :type log: Log
        """

        self.hits += 1
        self.visitors[(log.ip, log.user)] += 1
        self.paths[log.path] += 1
        self.bandwidth += log.size
        self.methods[log.method] += 1

        section = log.path.split('/', 2)[1] if log.path else '/'
        self.sections[section] += 1

        status = str(log.status_code)
        status_kind = f"{status[0]}XX"
        self.status_codes.update([status, status_kind])
        if status_kind != "5XX":
            self.valid_requests += 1


class HTTPStatsSections(HTTPStats):
    """
    Collect statistics from Log instances with also sections statistics.
    """
    def __init__(self):
        super(HTTPStatsSections, self).__init__()
        self.sections_stats = {}

    def update(self, log: Log):
        """
        Collect `Log` metrics and add it to existing statistics
        :param log: a `Log` instance
        :type log: Log
        """
        super(HTTPStatsSections, self).update(log)
        # also collect sections statistics
        section = log.path.split('/', 2)[1] if log.path else '/'
        section_stats = self.sections_stats.setdefault(section, HTTPStats())
        section_stats.update(log)
