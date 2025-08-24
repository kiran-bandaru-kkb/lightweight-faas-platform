from rest_framework import status, viewsets

from gateway import models
from gateway.models import FunctionInvocation
from gateway.serializers import FunctionInvocationSerializer


# Create your views here.

class FunctionInvocationViewSet(viewsets.ModelViewSet):
    queryset = FunctionInvocation.objects.all().order_by('-timestamp')
    serializer_class = FunctionInvocationSerializer
