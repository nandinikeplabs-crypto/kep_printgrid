from django.urls import path
from . import views
from . import api_views

app_name = 'printers'

urlpatterns = [
    # Dashboard views
    path('list/', views.printer_list, name='printer_list'),
    path('toggle/<uuid:printer_id>/', views.printer_toggle_active, name='printer_toggle_active'),
    path('set-default/<uuid:printer_id>/', views.printer_set_default, name='printer_set_default'),
    path('assignments/', views.printer_assignments_view, name='printer_assignments'),
    path('reassign-queued/', views.reassign_queued_jobs_view, name='reassign_queued_jobs'),

    # Connector REST APIs
    path('api/connector/register/', api_views.ConnectorRegisterAPIView.as_view(), name='api_connector_register'),
    path('api/connector/heartbeat/', api_views.ConnectorHeartbeatAPIView.as_view(), name='api_connector_heartbeat'),
    path('api/connector/poll-jobs/', api_views.ConnectorPollJobsAPIView.as_view(), name='api_connector_poll_jobs'),
    path('api/connector/update-job-status/', api_views.ConnectorUpdateJobStatusAPIView.as_view(), name='api_connector_update_job_status'),
]
