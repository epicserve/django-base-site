bind = "0.0.0.0:8080"

# Trust X-Forwarded-* headers from any source, because the only thing that can
# reach gunicorn is Traefik (inside the Docker network). Without this, gunicorn
# defaults to 127.0.0.1 and drops Traefik's forwarded headers, so Django sees
# http://<internal>:8080 and rejects POSTs on CSRF origin checks.
forwarded_allow_ips = "*"

# Concurrency: mirrors the previous uwsgi setup (4 workers × 2 threads).
workers = 4
worker_class = "gthread"
threads = 2

# Timeouts. `timeout` is gunicorn's equivalent of uwsgi's harakiri; any worker
# that doesn't respond for this long is killed. `graceful_timeout` is how long
# in-flight requests get to finish before a worker recycle / shutdown kills them.
timeout = 120
graceful_timeout = 30
keepalive = 5

# Recycle workers after max_requests ± jitter to stagger restarts and avoid a
# coordinated wave of worker replacement (the previous uwsgi config had no
# stagger, which was one of the suspected 502 sources on production).
max_requests = 5000
max_requests_jitter = 500

# Preload the app in the master before forking — saves memory, and together
# with the gthread worker + max-requests jitter is safe for recycling.
preload_app = True

# Gunicorn's own access + error loggers write to stderr/stdout so Docker picks
# them up. Django-level logs (django.request, etc.) still flow through the
# LOGGING dict in config.settings and get JSON-formatted.
accesslog = "-"
errorlog = "-"
