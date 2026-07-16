from django.db import models


class FraudCase(models.Model):
  RISK_LOW = 'LOW'
  RISK_MEDIUM = 'MEDIUM'
  RISK_HIGH = 'HIGH'

  RISK_LEVEL_CHOICES = [
    (RISK_LOW, 'Low'),
    (RISK_MEDIUM, 'Medium'),
    (RISK_HIGH, 'High'),
  ]

  STATUS_PENDING = 'PENDING_REVIEW'
  STATUS_AI_ANALYZED = 'AI_ANALYZED'
  STATUS_MARKED_SAFE = 'MARKED_SAFE'
  STATUS_ESCALATED = 'ESCALATED'
  STATUS_CUSTOMER_VERIFICATION = 'CUSTOMER_VERIFICATION_SENT'

  STATUS_CHOICES = [
    (STATUS_PENDING, 'Pending Review'),
    (STATUS_AI_ANALYZED, 'AI Analyzed'),
    (STATUS_MARKED_SAFE, 'Marked Safe'),
    (STATUS_ESCALATED, 'Escalated to Investigation'),
    (STATUS_CUSTOMER_VERIFICATION, 'Customer Verification Sent'),
  ]

  CHANNEL_ATM = 'ATM'
  CHANNEL_ONLINE = 'ONLINE'
  CHANNEL_MOBILE = 'MOBILE'
  CHANNEL_BRANCH = 'BRANCH'

  CHANNEL_CHOICES = [
    (CHANNEL_ATM, 'ATM'),
    (CHANNEL_ONLINE, 'Online'),
    (CHANNEL_MOBILE, 'Mobile'),
    (CHANNEL_BRANCH, 'Branch'),
  ]

  transaction_id = models.CharField(max_length=50, unique=True)
  customer_id = models.CharField(max_length=50)
  customer_name = models.CharField(max_length=200)
  amount = models.DecimalField(max_digits=12, decimal_places=2)
  average_customer_amount = models.DecimalField(max_digits=12, decimal_places=2)
  transaction_time = models.DateTimeField()
  location = models.CharField(max_length=200)
  usual_location = models.CharField(max_length=200)
  channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
  device_id = models.CharField(max_length=100, blank=True)
  is_new_device = models.BooleanField(default=False)
  beneficiary_type = models.CharField(max_length=50)
  is_new_beneficiary = models.BooleanField(default=False)
  failed_login_attempts = models.IntegerField(default=0)
  previous_fraud_flag = models.BooleanField(default=False)
  initial_risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
  risk_score = models.IntegerField(default=0)
  status = models.CharField(
    max_length=50,
    choices=STATUS_CHOICES,
    default=STATUS_PENDING,
  )
  assigned_to = models.CharField(max_length=100)
  ai_summary = models.TextField(blank=True)
  ai_recommendation = models.TextField(blank=True)
  customer_message = models.TextField(blank=True)

  verification_transcript = models.TextField(blank=True)
  elevenlabs_conversation_id = models.CharField(
    max_length=150,
    blank=True,
    )

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['-transaction_time']
    verbose_name = 'Fraud Case'
    verbose_name_plural = 'Fraud Cases'

  def __str__(self):
    return f'{self.transaction_id} - {self.customer_name}'

  @property
  def is_high_risk(self):
    return self.initial_risk_level == self.RISK_HIGH

  @property
  def allows_ai_automation(self):
    return self.initial_risk_level in (self.RISK_LOW, self.RISK_MEDIUM)

  @property
  def risk_badge_class(self):
    return {
      self.RISK_LOW: 'badge-low',
      self.RISK_MEDIUM: 'badge-medium',
      self.RISK_HIGH: 'badge-high',
    }.get(self.initial_risk_level, 'badge-pending')

  @property
  def amount_ratio(self):
    if self.average_customer_amount <= 0:
      return 0
    return round(float(self.amount) / float(self.average_customer_amount), 1)

  @property
  def status_badge_class(self):
    return {
      self.STATUS_PENDING: 'badge-pending',
      self.STATUS_AI_ANALYZED: 'badge-info',
      self.STATUS_MARKED_SAFE: 'badge-low',
      self.STATUS_ESCALATED: 'badge-high',
      self.STATUS_CUSTOMER_VERIFICATION: 'badge-info',
    }.get(self.status, 'badge-pending')
