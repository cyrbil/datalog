#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


logger = logging.getLogger(__name__)


class ConsumersFeeder(object):
    """
    Simple class that forward an element to a group of consumers
    """

    def __init__(self):
        self.consumers = []
        self.add_consumer = self.consumers.append
        self.remove_consumer = self.consumers.remove

    def feed_consumers(self, *args, **kwargs):
        for consumer in self.consumers:
            try:
                consumer(*args, **kwargs)
            except Exception as err:
                logger.error(f"{consumer!r} has failed to consume data", exc_info=err)
                raise
