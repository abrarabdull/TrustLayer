"""
Customer notification simulation service.
"""

from dataclasses import dataclass

from cases.models import FraudCase


@dataclass
class NotificationResult:
  success: bool
  message: str
  customer_message: str
  channel: str


DEFAULT_VERIFICATION_MESSAGE = (
  'Hello, we noticed a transaction that requires your confirmation to help protect '
  'your account. Did you authorize this transaction? Please confirm Yes or No.'
)


def prepare_verification_notification(case: FraudCase) -> NotificationResult:
  """Simulate preparing and sending a customer verification notification."""
  if case.is_high_risk:
    return NotificationResult(
      success=False,
      message='High-risk cases cannot receive automated customer notifications.',
      customer_message='',
      channel='',
    )

  customer_message = case.customer_message or DEFAULT_VERIFICATION_MESSAGE
  channel = _preferred_channel(case)

  case.customer_message = customer_message
  case.status = FraudCase.STATUS_CUSTOMER_VERIFICATION
  case.save(update_fields=['customer_message', 'status', 'updated_at'])

  return NotificationResult(
    success=True,
    message='Verification notification was prepared/sent for demo purposes only.',
    customer_message=customer_message,
    channel=channel,
  )


def _preferred_channel(case: FraudCase) -> str:
  if case.channel in (FraudCase.CHANNEL_MOBILE, FraudCase.CHANNEL_ONLINE):
    return 'SMS / Push Notification'
  return 'Email'
