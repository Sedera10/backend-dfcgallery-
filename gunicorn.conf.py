import os

# Bind to the port provided by the cloud service
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Worker configuration
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout settings
timeout = 120
keepalive = 2

# Performance tuning
preload_app = True
worker_tmp_dir = "/dev/shm"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'