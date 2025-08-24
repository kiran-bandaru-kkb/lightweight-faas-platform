from django.contrib import admin

from .models import Function, Deployment, WorkerNode, FunctionInstance, InvocationRequest



@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name', )

admin.site.register(Deployment)
admin.site.register(WorkerNode)
admin.site.register(FunctionInstance)
admin.site.register(InvocationRequest)


# @admin.register(Deployment)
# class WorkerAdmin(admin.ModelAdmin):
#     list_display = ('id', )
#     list_filter = ('is_active', 'function')
#     search_fields = ('worker_id', )
#
# @admin.register(WorkerNode)
# class WorkerAdmin(admin.ModelAdmin):
#     list_display = ('id', 'worker_id', 'function', 'is_active', 'latest_used')
#     list_filter = ('is_active', 'function')
#     search_fields = ('worker_id', )
#
# @admin.register(FunctionInstance)
# class WorkerAdmin(admin.ModelAdmin):
#     list_display = ('id', 'worker_id', 'function', 'is_active', 'latest_used')
#     list_filter = ('is_active', 'function')
#     search_fields = ('worker_id', )
#
# @admin.register(InvocationRequest)
# class WorkerAdmin(admin.ModelAdmin):
#     list_display = ('id', 'worker_id', 'function', 'is_active', 'latest_used')
#     list_filter = ('is_active', 'function')
#     search_fields = ('worker_id', )


