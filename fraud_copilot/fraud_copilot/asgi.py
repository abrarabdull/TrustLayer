"""
ASGI config for fraud_copilot project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fraud_copilot.settings')

application = get_asgi_application()
