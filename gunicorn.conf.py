# gunicorn.conf.py
import os

# Configuración para Render
bind = f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"
workers = 1
threads = 8
timeout = 120
worker_class = 'gthread'

# Para aplicaciones Dash
proc_name = 'dashapp'
preload_app = True