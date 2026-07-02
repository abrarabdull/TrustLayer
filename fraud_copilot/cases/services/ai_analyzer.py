"""
AI-powered fraud case analysis with OpenAI integration and mock fallback.
"""

import json
import logging
from dataclasses import dataclass

from django.conf import settings

from .risk_engine import assess_case

logger = logging.getLogger(__name__)


@dataclass
class AIAnalysisResult:
  risk_score: int
  risk_level: str
  analyst_summary: str
  suspicious_reasons: list[str]
  low_medium_rationale: str
  recommended_action: str
  customer_message: str
  is_mock: bool = False


def _build_mock_analysis(case, assessment) -> AIAnalysisResult:
  risk_level = assessment.level
  customer_first = case.customer_name.split()[0]

  if risk_level == 'HIGH':
    analyst_summary = (
      f'Case {case.transaction_id} for customer {case.customer_name} presents multiple '
      f'converging risk signals with a computed score of {assessment.score}/100. '
      f'This case exceeds automated handling thresholds and requires immediate human review '
      f'by the assigned analyst or Investigation team.'
    )
    low_medium_rationale = (
      'This case is classified as HIGH risk and is outside the scope of AI Co-Pilot automation. '
      'Manual review is mandatory before any customer contact.'
    )
    recommended = 'Escalate to Investigation'
    customer_message = ''
  elif risk_level == 'MEDIUM':
    analyst_summary = (
      f'Transaction {case.transaction_id} shows gray-area characteristics typical of '
      f'account takeover or first-party fraud patterns. The {case.channel} channel transfer '
      f'of {case.amount:,.2f} warrants verification but does not meet high-severity thresholds. '
      f'AI Co-Pilot recommends a structured customer confirmation workflow.'
    )
    low_medium_rationale = (
      f'Score of {assessment.score}/100 places this in the medium-risk band. '
      f'Some indicators are present ({len(assessment.reasons)} flagged) but the pattern '
      f'is consistent with legitimate edge cases that benefit from customer verification '
      f'rather than immediate escalation.'
    )
    recommended = assessment.recommended_action
    customer_message = (
      f'Hello {customer_first}, we noticed a transaction on your account that requires '
      f'your confirmation to help protect your account. Did you authorize a recent '
      f'{case.channel.lower()} transaction? Please confirm Yes or No.'
    )
  else:
    analyst_summary = (
      f'Transaction {case.transaction_id} triggered a routine monitoring alert. '
      f'After analysis, risk indicators are minimal and the activity appears consistent '
      f'with the customer\'s profile. Recommended for quick analyst review and likely closure.'
    )
    low_medium_rationale = (
      f'Low risk score of {assessment.score}/100. Primary factors are within normal '
      f'variance for this customer segment. Suitable for AI-assisted triage and safe marking.'
    )
    recommended = 'Mark as Safe'
    customer_message = (
      f'Hello {customer_first}, we are reviewing activity on your account as a routine '
      f'security check. No action is needed at this time unless you notice unfamiliar activity.'
    )

  return AIAnalysisResult(
    risk_score=assessment.score,
    risk_level=risk_level,
    analyst_summary=analyst_summary,
    suspicious_reasons=assessment.reasons,
    low_medium_rationale=low_medium_rationale,
    recommended_action=recommended,
    customer_message=customer_message,
    is_mock=True,
  )


def _build_openai_prompt(case, assessment) -> str:
  return f"""You are a senior fraud analyst assistant. Analyze this fraud monitoring case and respond in JSON only.

Case details:
- Transaction ID: {case.transaction_id}
- Customer: {case.customer_name} (ID: {case.customer_id})
- Amount: {case.amount} (Average: {case.average_customer_amount})
- Channel: {case.channel}
- Location: {case.location} (Usual: {case.usual_location})
- New device: {case.is_new_device}
- New beneficiary: {case.is_new_beneficiary} ({case.beneficiary_type})
- Failed logins: {case.failed_login_attempts}
- Previous fraud flag: {case.previous_fraud_flag}
- Initial risk level: {case.initial_risk_level}
- Computed risk score: {assessment.score}
- Risk reasons: {', '.join(assessment.reasons)}

Respond with this exact JSON structure:
{{
  "analyst_summary": "2-3 sentence professional summary",
  "suspicious_reasons": ["reason1", "reason2"],
  "low_medium_rationale": "Why this is low/medium risk or why high risk needs manual review",
  "recommended_action": "One of: Mark as Safe, Send Customer Verification Notification, Request More Information, Escalate to Investigation",
  "customer_message": "Brief customer verification message without sensitive details, or empty string for high risk"
}}

For HIGH risk cases, recommended_action must be "Escalate to Investigation" and customer_message must be empty."""


def _call_openai(case, assessment) -> AIAnalysisResult | None:
  api_key = getattr(settings, 'OPENAI_API_KEY', '')
  if not api_key:
    return None

  try:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
      model='gpt-4o-mini',
      messages=[
        {
          'role': 'system',
          'content': 'You are a fraud monitoring AI co-pilot. Respond only with valid JSON.',
        },
        {'role': 'user', 'content': _build_openai_prompt(case, assessment)},
      ],
      temperature=0.3,
      max_tokens=800,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith('```'):
      content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()

    data = json.loads(content)
    return AIAnalysisResult(
      risk_score=assessment.score,
      risk_level=assessment.level,
      analyst_summary=data.get('analyst_summary', ''),
      suspicious_reasons=data.get('suspicious_reasons', assessment.reasons),
      low_medium_rationale=data.get('low_medium_rationale', ''),
      recommended_action=data.get('recommended_action', assessment.recommended_action),
      customer_message=data.get('customer_message', ''),
      is_mock=False,
    )
  except Exception as exc:
    logger.warning('OpenAI analysis failed, using mock fallback: %s', exc)
    return None


def analyze_case(case) -> AIAnalysisResult:
  """Run AI analysis on a fraud case with OpenAI or mock fallback."""
  assessment = assess_case(case)

  if case.is_high_risk:
    result = _build_mock_analysis(case, assessment)
    result.analyst_summary = (
      'High-risk case detected. AI Co-Pilot automation is disabled for this alert. '
      'Please proceed with manual review or escalate to the Investigation team.'
    )
    result.recommended_action = 'Escalate to Investigation'
    result.customer_message = ''
    result.low_medium_rationale = (
      'This case is classified as HIGH risk based on initial detection and computed score. '
      'Automated AI handling is not permitted.'
    )
    return result

  openai_result = _call_openai(case, assessment)
  if openai_result:
    return openai_result

  return _build_mock_analysis(case, assessment)
