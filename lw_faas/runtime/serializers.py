from rest_framework import permissions, serializers
from .models import RuntimeExecution


class RuntimeExecutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = RuntimeExecution
        fields = '__all__'