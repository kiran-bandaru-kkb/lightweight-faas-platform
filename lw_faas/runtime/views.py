from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
import uuid
from orchestrator.models import WorkerNode, FunctionInstance

class WorkerHeartbeatView(APIView):
    """
    API endpoint for a worker node to check in and update its status.
    POST /api/runtime/heartbeat/
    """
    authentication_classes = [] # Use strong authentication like mTLS or shared secrets
    permission_classes = []

    def post(self, request):
        # Expecting: { "hostname": "worker-1", "ip_address": "192.168.1.10", "max_memory_mb": 8192, "available_memory_mb": 4096 }
        hostname = request.data.get('hostname')
        if not hostname:
            raise ValidationError("Missing 'hostname'.")

        worker, created = WorkerNode.objects.update_or_create(
            hostname=hostname,
            defaults={
                'ip_address': request.data.get('ip_address'),
                'max_memory_mb': request.data.get('max_memory_mb', 0),
                'available_memory_mb': request.data.get('available_memory_mb', 0),
                'status': 'ONLINE'
            }
        )
        # Update the 'last_heartbeat' field is handled by the model's `auto_now=True`
        return Response({"worker_id": str(worker.id)}, status=status.HTTP_200_OK)

class InstanceReadyView(APIView):
    """
    API endpoint for a runtime_host to register itself as ready.
    POST /api/runtime/instance_ready/
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Expecting: { "instance_id": "uuid", "port": 8080 }
        instance_id = request.data.get('instance_id')
        port = request.data.get('port')

        if not instance_id or not port:
            raise ValidationError("Missing 'instance_id' or 'port'.")

        try:
            instance = FunctionInstance.objects.get(id=instance_id)
            instance.port = port
            instance.status = 'RUNNING'
            instance.save()
            return Response({"status": "registered"})
        except FunctionInstance.DoesNotExist:
            raise ValidationError("Invalid instance_id.")