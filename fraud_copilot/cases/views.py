from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import FraudCase
from .services.ai_analyzer import analyze_case
from .services.notification_service import prepare_verification_notification
from .services.risk_engine import assess_case

from .services.n8n_service import send_demo_case_to_n8n
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.elevenlabs_service import get_conversation_transcript

def _apply_filters(queryset, request):
  risk = request.GET.get('risk', '')
  status = request.GET.get('status', '')
  channel = request.GET.get('channel', '')

  if risk:
    queryset = queryset.filter(initial_risk_level=risk)
  if status:
    queryset = queryset.filter(status=status)
  if channel:
    queryset = queryset.filter(channel=channel)

  return queryset, risk, status, channel


def dashboard(request):
  cases = FraudCase.objects.all()
  cases, risk_filter, status_filter, channel_filter = _apply_filters(cases, request)

  stats = {
    'total': FraudCase.objects.count(),
    'low': FraudCase.objects.filter(initial_risk_level=FraudCase.RISK_LOW).count(),
    'medium': FraudCase.objects.filter(initial_risk_level=FraudCase.RISK_MEDIUM).count(),
    'high': FraudCase.objects.filter(initial_risk_level=FraudCase.RISK_HIGH).count(),
    'pending': FraudCase.objects.filter(status=FraudCase.STATUS_PENDING).count(),
  }

  context = {
    'page_title': 'Dashboard',
    'cases': cases,
    'stats': stats,
    'risk_filter': risk_filter,
    'status_filter': status_filter,
    'channel_filter': channel_filter,
    'risk_choices': FraudCase.RISK_LEVEL_CHOICES,
    'status_choices': FraudCase.STATUS_CHOICES,
    'channel_choices': FraudCase.CHANNEL_CHOICES,
  }
  return render(request, 'cases/dashboard.html', context)


def cases_list(request):
  return dashboard(request)


def case_detail(request, pk):
  case = get_object_or_404(FraudCase, pk=pk)
  assessment = assess_case(case)

  context = {
    'page_title': f'Case {case.transaction_id}',
    'case': case,
    'assessment': assessment,
    'show_ai_warning': case.is_high_risk,
  }
  return render(request, 'cases/case_detail.html', context)


def analyze_case_view(request, pk):
  case = get_object_or_404(FraudCase, pk=pk)

  if case.is_high_risk:
    messages.error(
      request,
      'High-risk cases cannot be analyzed by the AI Co-Pilot. '
      'Please escalate to Investigation or perform manual review.',
    )
    return redirect('case_detail', pk=pk)

  result = analyze_case(case)

  case.risk_score = result.risk_score
  case.ai_summary = result.analyst_summary
  case.ai_recommendation = result.recommended_action
  case.customer_message = result.customer_message
  case.status = FraudCase.STATUS_AI_ANALYZED
  case.save()

  context = {
    'page_title': f'AI Analysis - {case.transaction_id}',
    'case': case,
    'result': result,
  }
  return render(request, 'cases/analyze_result.html', context)


@require_POST
def mark_safe(request, pk):
  case = get_object_or_404(FraudCase, pk=pk)

  if case.is_high_risk:
    messages.error(request, 'High-risk cases cannot be marked safe without manual investigation.')
    return redirect('case_detail', pk=pk)

  case.status = FraudCase.STATUS_MARKED_SAFE
  case.save(update_fields=['status', 'updated_at'])
  messages.success(request, f'Case {case.transaction_id} marked as safe.')
  return redirect('case_detail', pk=pk)


@require_POST
def escalate_case(request, pk):
  case = get_object_or_404(FraudCase, pk=pk)
  case.status = FraudCase.STATUS_ESCALATED
  case.save(update_fields=['status', 'updated_at'])
  messages.warning(request, f'Case {case.transaction_id} escalated to Investigation team.')
  return redirect('case_detail', pk=pk)


@require_POST
def send_notification(request, pk):
  case = get_object_or_404(FraudCase, pk=pk)

  if case.is_high_risk:
    messages.error(request, 'Customer notifications are not available for high-risk cases.')
    return redirect('case_detail', pk=pk)

  result = prepare_verification_notification(case)

  if result.success:
    messages.success(request, result.message)
  else:
    messages.error(request, result.message)

  return redirect('case_detail', pk=pk)


def ai_copilot_info(request):
  pending_ai = FraudCase.objects.filter(
    initial_risk_level__in=[FraudCase.RISK_LOW, FraudCase.RISK_MEDIUM],
    status=FraudCase.STATUS_PENDING,
  ).count()
  analyzed = FraudCase.objects.filter(status=FraudCase.STATUS_AI_ANALYZED).count()

  context = {
    'page_title': 'AI Co-Pilot',
    'pending_ai': pending_ai,
    'analyzed': analyzed,
  }
  return render(request, 'cases/ai_copilot.html', context)


def notifications_page(request):
  sent_cases = FraudCase.objects.filter(
    status=FraudCase.STATUS_CUSTOMER_VERIFICATION,
  )
  context = {
    'page_title': 'Notifications',
    'sent_cases': sent_cases,
  }
  return render(request, 'cases/notifications.html', context)


def about_page(request):
  context = {'page_title': 'About MVP'}
  return render(request, 'cases/about.html', context)
@require_POST
def start_demo_call(request):
    try:
        response = send_demo_case_to_n8n()

        data = response.json()

        case = FraudCase.objects.get(
            transaction_id="TXN-2026-00011"
        )

        case.elevenlabs_conversation_id = data.get(
            "conversation_id",
            ""
        )
        case.verification_transcript = ""
        case.save(update_fields=[
            "elevenlabs_conversation_id",
            "verification_transcript",
            "updated_at",
        ])

        messages.success(
            request,
            "تم إرسال الحالة وبدء مكالمة التحقق."
        )

    except Exception as exc:
        messages.error(
            request,
            f"تعذر بدء المكالمة: {exc}"
        )

    return redirect("dashboard")

@csrf_exempt
@require_POST
def save_transcript(request):
    try:
        data = json.loads(request.body)
        transaction_id = data.get("transaction_id")
        transcript = data.get("transcript", "")

        if not transaction_id:
            return JsonResponse(
                {"success": False, "error": "transaction_id is required"},
                status=400,
            )

        case = FraudCase.objects.get(transaction_id=transaction_id)
        case.verification_transcript = transcript
        case.save(update_fields=["verification_transcript", "updated_at"])

        return JsonResponse({
            "success": True,
            "transaction_id": transaction_id,
        })

    except FraudCase.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Transaction not found"},
            status=404,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON"},
            status=400,
        )
    
@require_POST
def load_transcript(request, pk):
    case = get_object_or_404(FraudCase, pk=pk)

    if not case.elevenlabs_conversation_id:
        messages.error(request, "لا يوجد رقم محادثة محفوظ لهذه الحالة.")
        return redirect("case_detail", pk=pk)

    try:
        transcript = get_conversation_transcript(
            case.elevenlabs_conversation_id
        )

        if not transcript:
            messages.warning(
                request,
                "المكالمة لم تنتهِ بعد أو الـTranscript غير جاهز."
            )
            return redirect("case_detail", pk=pk)

        case.verification_transcript = transcript
        case.save(update_fields=[
            "verification_transcript",
            "updated_at",
        ])

        messages.success(request, "تم تحميل آخر مكالمة.")

    except Exception as exc:
        messages.error(
            request,
            f"تعذر تحميل المكالمة: {exc}"
        )

    return redirect("case_detail", pk=pk)