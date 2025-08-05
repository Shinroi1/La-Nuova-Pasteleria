from django.contrib import admin
from . models import *

# Register your models here.
admin.site.register(Menu)
admin.site.register(NormalReservationTable)
admin.site.register(NormalReservationOrder)
admin.site.register(SessionDishHistory)
admin.site.register(UnavailableDateTime)
admin.site
