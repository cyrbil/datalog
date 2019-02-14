#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
This file defined the template that will be displayed
Everything is pretty much hardcoded, but you can edit some pieces
like colors without much trouble.

The template uses unprintable characters to switch colors, the character codepoint
is the color index in the COLORS array.

Single quote characters are spacers and use to facilitate creation of the template
by keeping table aligned. (it's still a pain in the ass to edit)
"""


# color map use during display, indexes are used in template
COLORS = [
    15,   # white
    249,  # gray
    82,   # green
    214,  # yellow
    164,  # red dark
    27,   # blue
    135,  # purple
    81,   # cyan
    160,  # red
]


# hard coded template elements
TPL_LINE_HEADER_END = 11

TPL_LINE_DETAIL_EMPTY = 10
TPL_LINE_DETAIL = 13
TPL_LINE_DETAIL_HEADER = 12
TPL_LINE_DETAILS_STATS_START = 14
TPL_LINE_DETAILS_STATS_END = 17
TPL_LINE_DETAILS_NONE = 11
TPL_LINE_DETAILS_END = 20
TPL_DETAILS_LEN = 6

TPL_LINE_ALERT_EMPTY = 19
TPL_LINE_ALERT_OK = 21
TPL_LINE_ALERT_KO = 22
TPL_LINE_ALERT_NONE = 20
TPL_LINE_ALERT_END = 23
TPL_ALERT_LEN = 6


# the template
TEMPLATE = """\1
  ┌─ \0Datalog HTTP Monitoring ''''''''''''''''''''''''''''''''''''\1─────────────────────┬───────────\0 Alerting Status: {alert_status:<2s} ''''''''''''''''''''''''''''''''''''''''''\1─┐
  │                                               ''''''''''''''''''''''''''''''''''''''''│                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │ \1Total Requests: \2{total_requests:>6s} \1Unique Visitors: \2{total_visitors:>5s}\1 '│ 200: \0{total_200:5s}\1 404: \0{total_404:5s}\1 5XX: \0{total_5XX:4s} ''''''''''''''''''''''\1│
  │ \1Valid Requests: \2{total_valid:>6s} \1Requested Files: \2{total_files:>5s}\1 '''''''│ 2XX: \0{total_2XX:5s}\1 3XX: \0{total_3XX:5s}\1 4XX: \0{total_4XX:4s} ''''''''''''''''''''''\1│
  │ \1Failed Requests: \2{total_fail:>5s} \1Bandwidth: \2'''''{total_bandwidth:>11s}\1 '''│ LogFile:\3 {log_file:<22s} '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\1│
  │                                               ''''''''''''''''''''''''''''''''''''''''│                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  ├─ \0Statistics for last {config_period:─<25s}'''''''''''''''''''''''''''''''''''''''''─┴─────────────────────────────────''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''┤
  │                                                                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │ Last update:\7 {period_date:<8s}\1 at\7 {period_time:<8s}\1                                               ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │                                                                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │ No data during period ...                                                       ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │''       Hits           Visitors      Bandwidth    Files    Section                ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │\4  {detail_hits:>5d} ({detail_hits_r:6.1%})\3   {detail_visitors:>5d} ({detail_visitors_r:6.1%})\5 {detail_bandwidth:>11s}\0     {detail_subsections:>4d}\6     {detail_path:<21s} '\1│
  │ - \0Total \1----------------------------------------------------------------------- ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │\4  {period_requests:>5d}\1 Hits\3       {period_visitors:>5d}\1 Visitors\5    {period_bandwidth:>8s}\0    {period_files:>5d}\2  {period_reqs_rate:>5s}\1 Reqs/s             ''''''''''│
  │ Status Codes - 200:\0 {period_200:3d}\1  404:\0 {period_404:3d}\1  5XX:\0 {period_5XX:3d}\1  2XX:\0 {period_2XX:3d}\1  3XX:\0 {period_3XX:3d}\1  4XX:\0 {period_4XX:3d}\1       ''''''│
  │                                                                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  ├─ \0Alerts History {alert_threshold:─<64s}''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''─┤
  │                                                                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │ No alerts history...                                                            ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │ \2High traffic recovered\1 at \7{alert_end}\1 - duration:\7 {alert_duration: <22s} '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\1│
  │ \10High traffic alert\1 - hits =\4 {alert_hits:>5s}\1, triggered at \7{alert_start}              ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\1│
  │ (Complete history at\3 {alert_log}\1)                                           ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  │                                                                                 ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''│
  └─────────────────────────────────────────────────────────────────────────────────''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''┘
"""
