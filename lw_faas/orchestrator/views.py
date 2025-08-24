from django.shortcuts import render
from rest_framework import viewsets, permissions

from .models import Worker, Function
from .serializers import  FunctionSerializer, WorkerSerializer

class FunctionViewSet(viewsets.ModelViewSet):
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer

class WorkerViewSet(viewsets.ModelViewSet):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer

