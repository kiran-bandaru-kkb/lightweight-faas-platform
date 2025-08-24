from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'functions', views.FunctionViewSet, basename='functions')
router.register(r'deployments', views.DeploymentViewSet, basename='deployment')
router.register(r'workers', views.WorkerNodeViewSet, basename='worker')
router.register(r'instances', views.FunctionInstanceViewSet, basename='instance')
router.register(r'invocations', views.InvocationRequestViewSet, basename='invocation')

urlpatterns = [
    path('', include(router.urls)),
]