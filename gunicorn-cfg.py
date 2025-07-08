# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import multiprocessing
import os

# Server socket
bind = '127.0.0.1:5005'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/home/dev/logs/gunicorn_access.log"
errorlog = "/home/dev/logs/gunicorn_error.log"
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'beautiland'

# Server mechanics
daemon = False
pidfile = '/home/dev/logs/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if using HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=core.settings_prod',
]

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True
capture_output = True
