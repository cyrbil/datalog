#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import logging
import argparse
import datetime

import faker
import isodate


logger = logging.getLogger(__name__)


class LogGenerator(object):
    """
    This class generate parametrized random log
    """
    def __init__(self, users, files, ips,
                 threshold_requests, threshold_period, threshold_duration_max, threshold_trigger_each):
        self.fake = fake = faker.Faker()
        self.methods = ((70, "GET"), (15, "POST"), (4, "PUT"), (11, "HEAD"))
        self.status_code = ((75, 200), (10, 404), (5, 403), (5, 500))
        self.users = list(fake.first_name() for _ in range(users))
        self.files = list(fake.uri_path() for _ in range(files))
        self.ips = list(fake.ipv4_public() for _ in range(ips))
        self.threshold_requests = threshold_requests
        self.threshold_period = threshold_period
        self.threshold_duration_max = threshold_duration_max
        self.threshold_trigger_each = threshold_trigger_each

    @staticmethod
    def random_bias(items):
        keys = (i[0] for i in items)
        number = random.uniform(0, sum(keys))
        current = 0
        for bias, item in items:
            current += bias
            if number <= current:
                return item

    def generate_log(self, when=None):
        """
        127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 123
        127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 234
        127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 200 34
        127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 503 12
        """
        ip = random.choice(self.ips)
        have_user = bool(random.getrandbits(1))
        user = random.choice(self.users) if have_user else '-'
        method = self.random_bias(self.methods)
        path = random.choice(self.files)
        status_code = self.random_bias(self.status_code)
        date = (when or datetime.datetime.utcnow())\
            .replace(tzinfo=datetime.timezone.utc)\
            .strftime("%d/%b/%Y:%H:%M:%S %z")
        si = random.randint(10, 300)
        return f'{ip} - {user} [{date}] "{method} /{path} HTTP/1.0" {status_code} {si}'

    def generate(self, generation_seconds=0, live=True):
        past_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=generation_seconds)
        threshold_start_stop_in = self.threshold_trigger_each
        current_threshold = False
        while True:
            yield self.generate_log(past_date)
            requests_per_seconds_max = self.threshold_requests
            frequency_min = 1 / requests_per_seconds_max

            if current_threshold:
                # continue spamming until threshold period ends
                wait = random.uniform(frequency_min / 5, frequency_min - (frequency_min / 5))
            else:
                wait = random.uniform(frequency_min + (frequency_min / 3), frequency_min * 3)

            now = datetime.datetime.utcnow()
            if past_date and now > past_date:
                past_date += datetime.timedelta(seconds=wait)
            elif live:
                time.sleep(wait)
                past_date = None
            else:
                break

            threshold_start_stop_in -= wait
            if not threshold_start_stop_in > 0:
                if not current_threshold:
                    current_threshold = True
                    threshold_start_stop_in = random.uniform(
                        self.threshold_period, self.threshold_duration_max + self.threshold_period)
                    logger.info(f"Entering spam mode for {threshold_start_stop_in} seconds")
                else:
                    current_threshold = False
                    threshold_start_stop_in = self.threshold_trigger_each
                    logger.info(f"Exiting spam mode for {threshold_start_stop_in} seconds")


def get_arg(args=None):
    def parse_iso_duration(duration_str):
        return isodate.parse_duration(duration_str).total_seconds()

    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", default=False)
    parser.add_argument("--period", type=parse_iso_duration, default="PT4H")
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--files", type=int, default=150)
    parser.add_argument("--ips", type=int, default=50)
    parser.add_argument("--monitoring-interval", type=int, default=10)
    parser.add_argument("--threshold-requests", type=int, default=100)
    parser.add_argument("--threshold-period", type=parse_iso_duration, default="PT2M")
    parser.add_argument("--threshold-duration-max", type=int, default=300)
    parser.add_argument("--threshold-trigger-each", type=int, default=600)

    return parser.parse_args(args)


def write_logs(log_generator, log_file, period, live):
    try:
        with open(log_file, "w+", encoding="utf-8") as fd:
            for log in log_generator.generate(period, live):
                fd.write(f"{log}\n")
                fd.flush()
    except (KeyboardInterrupt, SystemExit):
        pass

    try:
        os.remove(log_file)
    except OSError:
        pass


def main():
    args = get_arg().__dict__
    period, live = args.pop("period"), args.pop("live")
    generator = LogGenerator(**args)
    for log in generator.generate(period, live):
        print(log)


if __name__ == '__main__':
    main()
