pidfile = "/var/run/gunicorn_example.com.pid"
proc_name = "example.com"
workers = 1
bind = "unix:/tmp/gunicorn_example.com.sock"
