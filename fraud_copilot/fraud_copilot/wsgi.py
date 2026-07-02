"""
WSGI config for fraud_copilot project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fraud_copilot.settings')

application = get_wsgi_application()
