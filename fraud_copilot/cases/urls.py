from django.urls import path

from . import views

urlpatterns = [
  path('', views.dashboard, name='dashboard'),
  path('cases/', views.cases_list, name='cases_list'),
  path('cases/<int:pk>/', views.case_detail, name='case_detail'),
  path('cases/<int:pk>/analyze/', views.analyze_case_view, name='analyze_case'),
  path('cases/<int:pk>/mark-safe/', views.mark_safe, name='mark_safe'),
  path('cases/<int:pk>/escalate/', views.escalate_case, name='escalate_case'),
  path('cases/<int:pk>/notify/', views.send_notification, name='send_notification'),
  path('ai-copilot/', views.ai_copilot_info, name='ai_copilot'),
  path('notifications/', views.notifications_page, name='notifications'),
  path('about/', views.about_page, name='about'),
  path("demo-call/", views.start_demo_call, name="start_demo_call"),
  path(
    "save-transcript/",
    views.save_transcript,
    name="save_transcript",
),
path(
    "cases/<int:pk>/load-transcript/",
    views.load_transcript,
    name="load_transcript",
),
]
