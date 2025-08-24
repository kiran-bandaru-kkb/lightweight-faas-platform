from rest_framework.routers import  DefaultRouter
from .views import  FunctionViewSet, WorkerViewSet
router = DefaultRouter()

router.register('functions', FunctionViewSet, basename='function')
router.register('workers', WorkerViewSet, basename='worker')

urlpatterns = router.urls