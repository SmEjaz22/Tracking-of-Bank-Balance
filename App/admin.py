from django.contrib import admin

# Register your models here.
from .models import Total, Salary, Saving, Others

admin.site.register(Total)
admin.site.register(Salary)
admin.site.register(Saving)
admin.site.register(Others)
