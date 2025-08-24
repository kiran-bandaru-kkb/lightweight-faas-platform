from django.contrib import admin
from .models import FunctionInvocation


@admin.register(FunctionInvocation)
class FunctionInvocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'function_name', 'timestamp', 'status')
    list_filter = ('status', 'function_name')
    search_fields = ('function_name',)
