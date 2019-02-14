#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import datetime
import multiprocessing

from queue import Empty
from ipaddress import ip_address

from datalog_http_monitoring.consumers_feeder import ConsumersFeeder


logger = logging.getLogger(__name__)


class LogCollector(ConsumersFeeder):
    def __init__(self, log_files):
        super(LogCollector, self).__init__()

        self.log_files = log_files

        # check that file can be read early
        for log_file in log_files:
            assert os.path.exists(log_file), f"Log file {log_file!r} must exists"
            assert os.path.isfile(log_file), f"Log file {log_file!r} must be a file"
            assert os.access(log_file, os.R_OK), f"Log file {log_file!r} must be a readable"

        self.logs_queue = multiprocessing.Queue()
        self.watcher_process = multiprocessing.Process(
            name="LogWatcherProcess",
            target=self.watcher,
            args=(self.log_files, self.logs_queue),
            daemon=True
        )

    @staticmethod
    def watcher(log_files, logs_queue):
        try:
            logger.info(f"LogConsumerWatcher thread started on {log_files!r}")
            last_reads = {log_file: 0 for log_file in log_files}
            positions = {log_file: 0 for log_file in log_files}
            while True:
                # avoid using `stat` too frequently
                time.sleep(0.1)

                for log_file in log_files:
                    try:
                        last_reads[log_file], positions[log_file] = LogCollector.read_logs(
                            log_file, logs_queue, last_reads[log_file], positions[log_file])
                    except AssertionError:
                        # file has not changed since last read
                        pass
                    except IOError as err:
                        logger.error(f"Unable to read {log_file!r}", exc_info=err)
                    except Exception as err:
                        logger.error(f"Unable to collect {log_file!r} logs", exc_info=err)

        except (KeyboardInterrupt, SystemExit):
            pass

    @staticmethod
    def read_logs(log_file, logs_queue, last_read, position):
        # see if log file has changed
        stats = os.stat(log_file)
        has_changed = stats.st_mtime > last_read or stats.st_size > position
        assert has_changed, "No changes"
        last_read = stats.st_mtime

        # read new log lines
        # logger.debug(f"Detected new content in {log_file}")
        with open(log_file, "r", encoding="utf-8") as fd:
            fd.seek(position)
            while True:
                line = fd.readline()
                if not line:
                    # logger.debug(f"Finish reading logs in {log_file}")
                    break
                log = Log.from_string(line)
                if log:
                    logs_queue.put(log)
                    # note: we only move position once we successfully read
                    # a log line, that means that if we have garbage or incomplete
                    # line, we will retry reading until we got a log
                    position = fd.tell()

        return last_read, position

    def __iter__(self):
        while True:
            try:
                yield self.logs_queue.get(block=True, timeout=.5)
            except ValueError:
                # ignore semaphore release bug from Queue when debugging
                pass
            except Empty:
                yield EmptyLog()

    def run(self):
        self.watcher_process.start()
        for log in self:
            self.feed_consumers(log)


class Log(object):
    def __init__(self, ip, user, date, method, path, status_code, size):
        self.ip = ip
        self.user = user
        self.date = date
        self.method = method
        self.path = path
        self.status_code = status_code
        self.size = size

    @staticmethod
    def from_string(line):
        try:
            # 127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 123
            ip, _, user, date_str, tz_str, method, path, _, status_str, bytes_str, *other = line.split()
            return Log(
                ip=ip_address(ip),
                user=user if user != '-' else None,
                date=datetime.datetime.strptime(f"{date_str} {tz_str}", "[%d/%b/%Y:%H:%M:%S %z]"),
                method=method[1:],
                path=path,
                status_code=int(status_str),
                size=int(bytes_str),
            )
        except ValueError as err:
            logger.debug(f"Unable to parse log line {line!r} (reason: {err})")


class EmptyLog(Log):
    def __init__(self, date=None):
        if not date:
            date = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        super(EmptyLog, self).__init__(
            ip=None, user=None, method=None, path=None, status_code=None, size=None, date=date,)
