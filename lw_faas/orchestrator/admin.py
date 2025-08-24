from django.contrib import admin

from .models import Function, Worker


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name', )

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker_id', 'function', 'is_active', 'latest_used')
    list_filter = ('is_active', 'function')
    search_fields = ('worker_id', )


