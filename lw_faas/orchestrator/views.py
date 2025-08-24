from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Function, Deployment, WorkerNode, FunctionInstance, InvocationRequest
from .serializers import (FunctionSerializer, DeploymentSerializer,
                          WorkerNodeSerializer, FunctionInstanceSerializer,
                          InvocationRequestSerializer)

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class FunctionViewSet(viewsets.ModelViewSet):
    """
    API endpoint to manage Functions.
    """
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer
    permission_classes = [AllowAny]     #[IsAdminUser] # Or IsAuthenticated & custom permissions

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """Create a new Deployment for this Function."""
        function = self.get_object()
        # Logic to create a new Deployment snapshot
        # This would typically be in a service layer
        new_version = function.deployments.count() + 1
        deployment = Deployment.objects.create(
            function=function,
            version=new_version,
            comment=request.data.get('comment', ''),
            code_snapshot=function.code,
            requirements_snapshot=function.requirements,
            entry_point_snapshot=function.entry_point,
        )
        # Deactivate other deployments for this function
        function.deployments.exclude(id=deployment.id).update(is_active=False)
        deployment.is_active = True
        deployment.save()

        serializer = DeploymentSerializer(deployment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def invoke(self, request, pk=None):
        """Admin endpoint to directly invoke a function (for testing)."""
        # This would use the same internal logic the gateway uses
        # ... implementation would call the internal invocation service
        return Response({"detail": "Invocation triggered"}, status=status.HTTP_202_ACCEPTED)

class DeploymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view Deployment history.
    Read-only as they are created via the Function 'deploy' action.
    """
    serializer_class = DeploymentSerializer
    permission_classes = [AllowAny] # [IsAdminUser]
    queryset = Deployment.objects.all()

    def get_queryset(self):
        # Optionally filter by function_id from URL
        queryset = Deployment.objects.all()
        function_id = self.request.query_params.get('function_id')
        if function_id is not None:
            queryset = queryset.filter(function_id=function_id)
        return queryset

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Set this specific deployment as active."""
        deployment = self.get_object()
        # Deactivate all other deployments for this function
        Deployment.objects.filter(function=deployment.function).exclude(id=deployment.id).update(is_active=False)
        deployment.is_active = True
        deployment.save()
        serializer = self.get_serializer(deployment)
        return Response(serializer.data)

class WorkerNodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view and manage Worker nodes.
    'status' updates might be done via a separate API from the nodes themselves.
    """
    queryset = WorkerNode.objects.all()
    serializer_class = WorkerNodeSerializer
    permission_classes = [AllowAny] # [IsAdminUser]

class FunctionInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view currently running Function Instances.
    """
    serializer_class = FunctionInstanceSerializer
    permission_classes = [AllowAny] # [IsAdminUser]

    def get_queryset(self):
        queryset = FunctionInstance.objects.select_related('deployment__function', 'worker')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        return queryset

class InvocationRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view Invocation history and logs.
    """
    serializer_class = InvocationRequestSerializer
    permission_classes = [AllowAny] # [IsAdminUser]
    filterset_fields = ['function', 'deployment', 'status', 'is_cold_start']

    def get_queryset(self):
        queryset = InvocationRequest.objects.select_related('function', 'deployment', 'instance').all()
        # Add filtering for date ranges, etc.
        return queryset