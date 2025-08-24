from rest_framework import serializers
from .models import Function, Deployment, WorkerNode, FunctionInstance, InvocationRequest


class FunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Function
        fields = '__all__'

class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = '__all__'


class WorkerNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerNode
        fields = '__all__'


class FunctionInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionInstance
        fields = '__all__'


class InvocationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvocationRequest
        fields = '__all__'

