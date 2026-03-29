from django.contrib import admin

# Register your models here.
from .models import Pocket, Transaction, PatternRule, DeviceToken

admin.site.register(Pocket)
admin.site.register(Transaction)
admin.site.register(PatternRule)
admin.site.register(DeviceToken)

