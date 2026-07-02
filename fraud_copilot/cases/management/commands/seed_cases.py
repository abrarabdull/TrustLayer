import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from cases.models import FraudCase
from cases.services.risk_engine import assess_case


class Command(BaseCommand):
  help = 'Seed the database with synthetic fraud monitoring cases'

  def add_arguments(self, parser):
    parser.add_argument(
      '--clear',
      action='store_true',
      help='Clear existing cases before seeding',
    )

  def handle(self, *args, **options):
    seed_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'seed_cases.json'

    if not seed_path.exists():
      self.stderr.write(self.style.ERROR(f'Seed file not found: {seed_path}'))
      return

    if options['clear']:
      count = FraudCase.objects.count()
      FraudCase.objects.all().delete()
      self.stdout.write(f'Cleared {count} existing cases.')

    with open(seed_path) as f:
      cases_data = json.load(f)

    created = 0
    skipped = 0

    for entry in cases_data:
      if FraudCase.objects.filter(transaction_id=entry['transaction_id']).exists():
        skipped += 1
        continue

      tx_time = datetime.fromisoformat(entry['transaction_time'])
      if timezone.is_naive(tx_time):
        tx_time = timezone.make_aware(tx_time)

      case = FraudCase(
        transaction_id=entry['transaction_id'],
        customer_id=entry['customer_id'],
        customer_name=entry['customer_name'],
        amount=Decimal(entry['amount']),
        average_customer_amount=Decimal(entry['average_customer_amount']),
        transaction_time=tx_time,
        location=entry['location'],
        usual_location=entry['usual_location'],
        channel=entry['channel'],
        device_id=entry.get('device_id', ''),
        is_new_device=entry['is_new_device'],
        beneficiary_type=entry['beneficiary_type'],
        is_new_beneficiary=entry['is_new_beneficiary'],
        failed_login_attempts=entry['failed_login_attempts'],
        previous_fraud_flag=entry['previous_fraud_flag'],
        initial_risk_level=entry['initial_risk_level'],
        status=entry.get('status', FraudCase.STATUS_PENDING),
        assigned_to=entry['assigned_to'],
      )

      assessment = assess_case(case)
      case.risk_score = assessment.score
      case.save()
      created += 1

    self.stdout.write(
      self.style.SUCCESS(
        f'Seeding complete: {created} created, {skipped} skipped. '
        f'Total cases: {FraudCase.objects.count()}'
      )
    )

    low = FraudCase.objects.filter(initial_risk_level='LOW').count()
    medium = FraudCase.objects.filter(initial_risk_level='MEDIUM').count()
    high = FraudCase.objects.filter(initial_risk_level='HIGH').count()
    self.stdout.write(f'  Low: {low} | Medium: {medium} | High: {high}')
