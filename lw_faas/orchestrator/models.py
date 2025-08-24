import uuid

from django.db import models

class Function(models.Model):
    """
        Represents the deployment package and configuration for a serverless function.
        """
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)    # e.g., "user-profile-processor"
    description = models.TextField(blank=True)
    code = models.TextField(help_text="The raw Python source code of the function.")    # Source Code & Dependencies
    requirements = models.TextField(
        blank=True,
        help_text="Contents of requirements.txt for the function's dependencies."
    )
    entry_point = models.CharField(
        max_length=255,
        default="handle",
        help_text="The name of the function to invoke (e.g., 'handle', 'main')."
    )   # Resource Configuration
    memory_mb = models.PositiveIntegerField(default=128)  # Memory limit
    timeout_seconds = models.PositiveIntegerField(default=30)  # Execution timeout
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.id})"


class Deployment(models.Model):
    """
    A specific revision (snapshot) of a Function that can be deployed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    function = models.ForeignKey(Function, on_delete=models.CASCADE, related_name='deployments')
    version = models.PositiveIntegerField()  # e.g., 1, 2, 3...
    comment = models.CharField(max_length=255, blank=True)
    code_snapshot = models.TextField()  # Snapshot the code and config at the time of deployment
    requirements_snapshot = models.TextField()
    entry_point_snapshot = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False, help_text="Is this the live deployment?")

    class Meta:
        unique_together = ['function', 'version']  # Ensure version is unique per function
        ordering = ['function', '-version']

    def __str__(self):
        return f"{self.function.name} - v{self.version} ({'Active' if self.is_active else 'Inactive'})"


class WorkerNode(models.Model):
    """
    Represents a host machine that can execute functions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hostname = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    status = models.CharField(
        max_length=20,
        choices=(('ONLINE', 'Online'), ('OFFLINE', 'Offline'), ('DRAINING', 'Draining')),
        default='ONLINE'
    )
    last_heartbeat = models.DateTimeField(auto_now=True)  # Updated by the worker regularly
    max_memory_mb = models.PositiveIntegerField()      # Resource capacity
    available_memory_mb = models.PositiveIntegerField()  # Could be calculated, but stored for simplicity

    def __str__(self):
        return f"{self.hostname} ({self.status})"


class FunctionInstance(models.Model):
    """
    Represents an active (warm) instance of a function ready to handle requests.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerNode, on_delete=models.CASCADE)

    # Instance details
    status = models.CharField(
        max_length=20,
        choices=(
            ('PENDING', 'Pending'),  # Allocated but not yet ready
            ('RUNNING', 'Running'),  # Alive and ready to receive requests
            ('IDLE', 'Idle'),        # Running but no recent requests (maybe scaled down)
            ('ERROR', 'Error'),      # Crashed or unhealthy
        ),
        default='PENDING'
    )
    port = models.PositiveIntegerField()    # The port on the worker node where runtime_host is listening
    started_at = models.DateTimeField(auto_now_add=True)    # Track usage for scaling and cleanup
    last_accessed = models.DateTimeField(auto_now=True)  # Updated on every request

    class Meta:
        unique_together = ['worker', 'port']  # A port can only be used by one instance per worker

    def get_url(self):
        return f"http://{self.worker.ip_address}:{self.port}"

    def __str__(self):
        return f"Instance of {self.deployment.function.name} on {self.worker.hostname}:{self.port}"


class InvocationRequest(models.Model):
    """
    A log of every function invocation request.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    function = models.ForeignKey(Function, on_delete=models.CASCADE)
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE)  # Snapshot of which version was called
    instance = models.ForeignKey(FunctionInstance, on_delete=models.SET_NULL, null=True, blank=True) # Could be null if cold start failed

    # Request details
    request_id = models.CharField(max_length=255)  # Unique ID for this specific request
    request_body = models.TextField(blank=True, null=True)  # Careful with PII/size, might just store metadata
    request_headers = models.JSONField(default=dict)

    # Response details
    response_body = models.TextField(blank=True, null=True)
    response_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict)

    # Execution metadata
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_cold_start = models.BooleanField()

    # Status
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('TIMEOUT', 'Timeout'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    error_message = models.TextField(blank=True)

    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    class Meta:
        indexes = [
            models.Index(fields=['function', 'start_time']),  # For function-specific metrics
            models.Index(fields=['request_id']),              # For fast lookup by request ID
        ]

    def __str__(self):
        return f"Invocation {self.request_id} - {self.function.name} - {self.status}"
