from django.urls import path
from . import views

urlpatterns = [
    path('heartbeat/', views.WorkerHeartbeatView.as_view(), name='worker-heartbeat'),
    path('instance_ready/', views.InstanceReadyView.as_view(), name='instance-ready'),
]