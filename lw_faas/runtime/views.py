from django.shortcuts import render
from rest_framework import viewsets

from .models import RuntimeExecution
from .serializers import RuntimeExecutionSerializer

class RuntimeExecutionViewSet(viewsets.ModelViewSet):
    queryset = RuntimeExecution.objects.all()
    serializer_class = RuntimeExecutionSerializer
