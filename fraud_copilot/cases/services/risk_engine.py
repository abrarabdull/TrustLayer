"""
Rule-based risk scoring engine for fraud case assessment.
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class RiskAssessment:
  score: int
  level: str
  reasons: list[str] = field(default_factory=list)
  recommended_action: str = ''


def _score_amount_ratio(amount: Decimal, average: Decimal) -> tuple[int, str | None]:
  if average <= 0:
    return 0, None
  ratio = float(amount) / float(average)
  if ratio >= 5:
    return 25, f'Transaction amount ({amount:,.2f}) is {ratio:.1f}x higher than customer average ({average:,.2f})'
  if ratio >= 3:
    return 18, f'Transaction amount is {ratio:.1f}x higher than typical customer spending'
  if ratio >= 2:
    return 10, f'Transaction amount moderately exceeds customer average ({ratio:.1f}x)'
  return 0, None


def _score_location(location: str, usual_location: str) -> tuple[int, str | None]:
  if location.strip().lower() != usual_location.strip().lower():
    return 15, f'Unusual location: transaction in {location}, customer usually transacts in {usual_location}'
  return 0, None


def _score_transaction_time(transaction_time) -> tuple[int, str | None]:
  hour = transaction_time.hour
  if hour < 6 or hour >= 23:
    return 10, f'Unusual transaction time: {transaction_time.strftime("%H:%M")} (outside typical hours)'
  if hour < 8 or hour >= 22:
    return 5, f'Transaction occurred during off-peak hours ({transaction_time.strftime("%H:%M")})'
  return 0, None


def _level_from_score(score: int) -> str:
  if score >= 70:
    return 'HIGH'
  if score >= 40:
    return 'MEDIUM'
  return 'LOW'


def _recommended_action(level: str) -> str:
  if level == 'HIGH':
    return 'Escalate to Investigation'
  if level == 'MEDIUM':
    return 'Send Customer Verification Notification'
  return 'Mark as Safe'


def assess_case(case) -> RiskAssessment:
  """Compute risk score, level, reasons, and recommended action for a case."""
  score = 0
  reasons: list[str] = []

  amount_pts, amount_reason = _score_amount_ratio(case.amount, case.average_customer_amount)
  score += amount_pts
  if amount_reason:
    reasons.append(amount_reason)

  if case.is_new_device:
    score += 15
    reasons.append('Transaction initiated from a new or unrecognized device')

  if case.is_new_beneficiary:
    score += 15
    reasons.append(f'Payment to a new beneficiary ({case.beneficiary_type})')

  loc_pts, loc_reason = _score_location(case.location, case.usual_location)
  score += loc_pts
  if loc_reason:
    reasons.append(loc_reason)

  if case.failed_login_attempts >= 5:
    score += 20
    reasons.append(f'{case.failed_login_attempts} failed login attempts before transaction')
  elif case.failed_login_attempts >= 3:
    score += 12
    reasons.append(f'{case.failed_login_attempts} failed login attempts detected')

  if case.previous_fraud_flag:
    score += 25
    reasons.append('Customer has a previous fraud flag on record')

  time_pts, time_reason = _score_transaction_time(case.transaction_time)
  score += time_pts
  if time_reason:
    reasons.append(time_reason)

  score = min(score, 100)
  level = _level_from_score(score)

  if not reasons:
    reasons.append('No significant risk indicators detected beyond routine monitoring')

  return RiskAssessment(
    score=score,
    level=level,
    reasons=reasons,
    recommended_action=_recommended_action(level),
  )
