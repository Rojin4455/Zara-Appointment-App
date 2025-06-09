from django.contrib import admin
from servicenet.models import GHLUser,GHLAppointment

# Register your models here.
admin.site.register(GHLUser)
admin.site.register(GHLAppointment)