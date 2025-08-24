from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import NotFound, ValidationError
import requests
import json
import uuid
from datetime import datetime
from orchestrator.models import Function, Deployment, FunctionInstance, InvocationRequest
from orchestrator.serializers import InvocationRequestSerializer

class InvokeView(APIView):
    """
    Public API endpoint to invoke a function by name.
    POST /invoke/<function_name>/
    """
    # Use appropriate permissions for your users (e.g., TokenAuthentication)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, function_name, *args, **kwargs):
        # 1. Get the function and its active deployment
        try:
            function = Function.objects.get(name=function_name, is_active=True)
            deployment = function.deployments.get(is_active=True)
        except (Function.DoesNotExist, Deployment.DoesNotExist):
            raise NotFound(detail="Function not found or no active deployment.")

        # 2. Prepare invocation log
        invocation_id = uuid.uuid4()
        invocation_log = InvocationRequest.objects.create(
            id=invocation_id,
            function=function,
            deployment=deployment,
            request_id=request.META.get('HTTP_X_REQUEST_ID', str(invocation_id)),
            request_body=json.dumps(request.data), # Be cautious with size/PII
            request_headers=dict(request.headers),
            start_time=datetime.now(),
            is_cold_start=False # Assume warm start, update if not
        )

        # 3. Find or launch a function instance (orchestrator logic)
        # This is simplified. In reality, this would be a complex service call.
        instance = self._get_available_instance(deployment)
        if not instance:
            # Trigger cold start logic
            instance = self._trigger_cold_start(deployment)
            invocation_log.is_cold_start = True
            invocation_log.save()

        # 4. Proxy the request to the worker node
        target_url = f"{instance.get_url()}/" # Points to runtime_host's server
        try:
            # Forward headers, body, etc.
            headers = {'Content-Type': 'application/json'}
            # You might forward auth headers or inject a specific one for the runtime
            resp = requests.post(
                target_url,
                data=json.dumps(request.data),
                headers=headers,
                timeout=function.timeout_seconds + 5 # Add buffer
            )
            response_data = resp.json()
            response_status = resp.status_code

        except requests.exceptions.Timeout:
            # Handle timeout
            response_status = status.HTTP_504_GATEWAY_TIMEOUT
            response_data = {"error": "Function execution timed out"}
            invocation_log.status = 'TIMEOUT'
        except requests.exceptions.ConnectionError:
            # Handle instance failure
            response_status = status.HTTP_503_SERVICE_UNAVAILABLE
            response_data = {"error": "Function instance unavailable"}
            instance.status = 'ERROR' # Mark instance as errored
            instance.save()
            invocation_log.status = 'FAILURE'
            invocation_log.error_message = "Connection to worker failed"
        except Exception as e:
            # Handle any other error
            response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_data = {"error": "Internal gateway error"}
            invocation_log.status = 'FAILURE'
            invocation_log.error_message = str(e)
        else:
            # Success path
            invocation_log.response_status_code = resp.status_code
            invocation_log.response_body = resp.text
            invocation_log.status = 'SUCCESS' if resp.ok else 'FAILURE'

        # 5. Finalize the invocation log
        invocation_log.end_time = datetime.now()
        invocation_log.save()

        # 6. Return the response to the client
        return Response(data=response_data, status=response_status)

    def _get_available_instance(self, deployment):
        """Finds a RUNNING or IDLE instance for the deployment."""
        try:
            # Simple strategy: find the most recently used IDLE instance
            return FunctionInstance.objects.filter(
                deployment=deployment,
                status__in=['RUNNING', 'IDLE'],
                worker__status='ONLINE'
            ).order_by('-last_accessed').first()
        except FunctionInstance.DoesNotExist:
            return None

    def _trigger_cold_start(self, deployment):
        """Complex logic to schedule a function on a worker."""
        # This is a massive simplification.
        # 1. Would find a suitable worker with capacity
        # 2. Would call the runtime management API on that worker to spawn an instance
        # 3. Would create and return a new FunctionInstance record with status 'PENDING'
        # 4. Would wait/poll for the instance to become 'RUNNING'
        # For the PoC, this is the core complexity to implement.
        raise NotImplementedError("Cold start logic not implemented for PoC.")
