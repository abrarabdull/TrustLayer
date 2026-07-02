from django.contrib import admin

from .models import FraudCase


@admin.register(FraudCase)
class FraudCaseAdmin(admin.ModelAdmin):
  list_display = (
    'transaction_id',
    'customer_name',
    'amount',
    'initial_risk_level',
    'status',
    'assigned_to',
    'transaction_time',
  )
  list_filter = ('initial_risk_level', 'status', 'channel')
  search_fields = ('transaction_id', 'customer_name', 'customer_id')
  readonly_fields = ('created_at', 'updated_at')
