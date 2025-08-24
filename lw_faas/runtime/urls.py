from rest_framework.routers import DefaultRouter
from .views import RuntimeExecutionViewSet
router = DefaultRouter()

router.register(r'executions', RuntimeExecutionViewSet, basename='runtime_execution')
urlpatterns = router.urls