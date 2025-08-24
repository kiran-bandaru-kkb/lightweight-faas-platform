from django.db import models

class FunctionInvocation(models.Model):
    function_name = models.CharField(max_length=255)
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    response = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.function_name} at {self.timestamp}"

    class Meta:
        ordering = ('-timestamp',)

