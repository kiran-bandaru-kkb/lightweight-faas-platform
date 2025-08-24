from django.contrib import admin
from .models import RuntimeExecution

@admin.register(RuntimeExecution)
class RuntimeExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker_id', 'executed_at', 'status')
    list_filter = ('status', 'worker_id')
    search_fields = ('worker_id', )
