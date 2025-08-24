from django.urls import path
from . import views

urlpatterns = [
    path('invoke/<str:function_name>/', views.InvokeView.as_view(), name='invoke-function'),
]