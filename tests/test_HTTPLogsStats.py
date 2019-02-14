#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

from unittest import TestCase

from datalog_http_monitoring.generate_logs import LogGenerator
from datalog_http_monitoring.log_collector import Log
from datalog_http_monitoring.http_logs_stats import HTTPLogsStats


class TestHTTPLogsStats(TestCase):
    def setUp(self):
        self.tmp_file = tempfile.mkstemp()[1]
        self.log_generator = LogGenerator(
            users=10,
            files=10,
            ips=10,
            threshold_requests=10,
            threshold_period=10,
            threshold_duration_max=10,
            threshold_trigger_each=10
        )
        self.http_log_stats = HTTPLogsStats(
            period=10,
            alert_period=10,
            alert_threshold=10,
            alert_output=self.tmp_file
        )

    def test_alerts_detected(self):
        # more of a functional test than unit test, but it covers all of http_logs_stats
        self.http_log_stats.all_stats.reset()
        for log in self.log_generator.generate(generation_seconds=60, live=False):
            self.http_log_stats.update(Log.from_string(log))

        assert self.http_log_stats.alerts, "An alert should have been triggered"
        assert os.path.getsize(self.tmp_file), "Alert should have been written to file"
