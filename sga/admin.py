from django.contrib import admin

from sga.models.associate import Associate
from sga.models.vehicle_sga import VehicleSGA
from sga.models.token import HinovaToken

admin.site.register(HinovaToken)
admin.site.register(Associate)
admin.site.register(VehicleSGA)