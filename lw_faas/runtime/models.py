from django.db import models

class RuntimeExecution(models.Model):
    worker_id = models.CharField(max_length=255)
    input_payload = models.JSONField()
    output_payload = models.JSONField(null=True, blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
