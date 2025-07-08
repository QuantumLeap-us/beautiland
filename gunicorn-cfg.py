# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

bind = '0.0.0.0:5005'
workers = 3
timeout = 120
accesslog = '-'
loglevel = 'info'
accesslog = "/home/dev/logs/gunicorn_access.log"
errorlog = "/home/dev/logs/gunicorn_error.log"
capture_output = True
enable_stdio_inheritance = True
