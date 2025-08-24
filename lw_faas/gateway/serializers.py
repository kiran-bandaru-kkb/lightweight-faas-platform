from rest_framework import serializers
from gateway.models import FunctionInvocation


class FunctionInvocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionInvocation
        fields = ['id', 'function_name', 'payload', 'timestamp', 'status', 'response']