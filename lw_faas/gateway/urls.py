from rest_framework.routers import DefaultRouter
from .views import FunctionInvocationViewSet
router = DefaultRouter()
router.register('invocations', FunctionInvocationViewSet, basename='function_invocation')
urlpatterns = router.urls