import requests
from django.conf import settings


def send_demo_case_to_n8n():
    response = requests.post(
        settings.N8N_WEBHOOK_URL,
        json={"demo": True},
        timeout=20,
    )
    response.raise_for_status()
    return response