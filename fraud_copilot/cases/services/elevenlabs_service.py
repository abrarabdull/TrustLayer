import requests
from django.conf import settings


def get_conversation_transcript(conversation_id):
    url = (
        "https://api.elevenlabs.io/v1/convai/conversations/"
        f"{conversation_id}"
    )

    response = requests.get(
        url,
        headers={
            "xi-api-key": settings.ELEVENLABS_API_KEY,
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    messages = data.get("transcript", [])

    lines = []

    for message in messages:
        role = message.get("role", "")
        text = message.get("message", "")

        if not text:
            continue

        speaker = "Sentinel" if role == "agent" else "Customer"
        lines.append(f"{speaker}: {text}")

    return "\n".join(lines)