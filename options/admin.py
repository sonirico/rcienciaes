from django.contrib import admin
from models import Option


class OptionAdmin(admin.ModelAdmin):
    fields = ('nice_name', 'value', 'auto_load')


admin.site.register(Option, OptionAdmin)
# Add
