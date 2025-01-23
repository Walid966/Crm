bind = "0.0.0.0:8080"
workers = 4
worker_class = "gevent"
timeout = 120
keepalive = 5
errorlog = "logs/error.log"
accesslog = "logs/access.log"
loglevel = "info" 