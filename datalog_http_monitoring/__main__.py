#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
import tempfile
import multiprocessing

from datalog_http_monitoring.generate_logs import write_logs


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Collect logs and display realtime formatted statistics")
    parser.add_argument("log_files", help="Files to collect logs from (default: %(default)s)",
                        metavar="LOGFILE", default=["/tmp/access.log"], nargs="*")
    parser.add_argument("--period", help="monitoring period to display statistics (default: %(default)s)",
                        default=10, type=int)
    parser.add_argument("--alert", help="minimum number of requests to trigger alert mode (default: %(default)s)",
                        metavar="THRESHOLD", default=10, type=int)
    parser.add_argument("--alert-period", help="period to look for threshold alert (default: %(default)s)",
                        default=120, type=int)
    parser.add_argument("--alert-file", help="where to store alerts details (default: %(default)s)",
                        default=os.path.join(tempfile.gettempdir(), "alerts.log"), type=str)
    parser.add_argument("--refresh", help="statistics display refresh delay (default: %(default)s)",
                        default=.1, type=float)
    parser.add_argument("--no-curses", help="fallback to simple print for display",
                        default=False, action="store_true")
    parser.add_argument("--demo", help="auto generate logs for debugging purpose",
                        default=False, action="store_true")
    parser.add_argument("--debug", help="show application debug information",
                        default=False, action="store_true")
    parser.add_argument("--debug-file", help="write application debug information to this file (default: stderr)",
                        metavar="FILE", default=sys.stderr, type=argparse.FileType("w+"))
    parser.add_argument("--debug-color", help="colorize application debug information (implies --debug)",
                        default=False, action="store_true")
    parsed_args = parser.parse_args(args)
    parsed_args.log_files = set(parsed_args.log_files)
    return parsed_args


def launch_log_generator(args):
    from datalog_http_monitoring.generate_logs import LogGenerator

    log_generator = LogGenerator(
        users=max(args.alert // 3, 30),
        files=max(args.alert // 4, 20),
        ips=max(args.alert // 3, 25),
        threshold_requests=args.alert,
        threshold_period=args.alert_period,
        threshold_duration_max=args.alert_period * 3,
        threshold_trigger_each=args.alert_period * 5
    )

    logging.info(f"Starting log generator with period {args.period} and threshold {args.alert}")

    for log_file in args.log_files:
        # empty test log files
        with open(log_file, "w+", encoding="utf-8"):
            pass

        multiprocessing.Process(
            name=f"GenerateLogs_{log_file}",
            target=write_logs,
            args=(log_generator, log_file, 6000, True),
            daemon=True
        ).start()


def run(args):
    args = parse_args(args)
    if args.debug or args.debug_color:
        if args.debug_color:
            import coloredlogs
            coloredlogs.install(stream=args.debug_file, level=logging.DEBUG, isatty=True)
        else:
            logging.basicConfig(stream=args.debug_file, level=logging.DEBUG)

    if args.demo:
        logging.getLogger("faker").setLevel(logging.INFO)
        launch_log_generator(args)

    from datalog_http_monitoring.cli_swag import CliSwag
    from datalog_http_monitoring.log_collector import LogCollector
    from datalog_http_monitoring.http_logs_stats import HTTPLogsStats

    # initialize classes
    collector = LogCollector(log_files=args.log_files)
    stats = HTTPLogsStats(
        period=args.period,
        alert_period=args.alert_period,
        alert_threshold=args.alert,
        alert_output=args.alert_file)

    with CliSwag(refresh_time=args.refresh, use_curses=not args.no_curses) as cli:
        # connect collected log to stats and stats to cli
        collector.add_consumer(stats.update)
        stats.add_consumer(cli.update)

        # collect log
        collector.run()


def main(args=None):
    try:
        run(args)
    except (KeyboardInterrupt, SystemExit):
        pass
    except AssertionError as err:
        print(f"Error: {err}\n", file=sys.stderr)


if __name__ == '__main__':
    main()
