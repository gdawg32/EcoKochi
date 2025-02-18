from django.contrib import admin
from core.models import *
# Register your models here.

admin.site.register(Ward)
admin.site.register(WardManager)
admin.site.register(WasteCollector)
admin.site.register(Resident)
admin.site.register(WasteCollectionActivity)
admin.site.register(WasteSchedule)
admin.site.register(WasteType)
admin.site.register(ResidentApplication)
