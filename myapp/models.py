# from datetime import datetime,timedelta
# from uuid import uuid4
from django.urls import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

class Menu(models.Model):
        
    dish_name = models.CharField(max_length=200, null=True)
    category = models.CharField(max_length=200, null=True)
    sub_category = models.CharField(max_length=200, default="None",)
    ingredients = models.CharField(max_length=200, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    image = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)  
    
    def __str__(self):
        return f"{self.dish_name} - {self.category} {self.sub_category}"

    def get_absolute_url(self):
        return reverse('dish_name', kwargs={'slug': self.slug})

class NormalReservationTable(models.Model):
    TABLESTATUS = (
        ('Reserved', 'Reserved'), 
        ('In progress', 'In progress'),
        ('Paid', 'Paid'),
        ('Completed', 'Completed'), # Means the customer/s is finished using the table
        ('No Show', 'No Show'),
        ('Cancelled', 'Cancelled'),     
        )
        
    fullname = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=50, null=True)
    phone = models.CharField(max_length=11, null=True)
    party_size = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(12)])    
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    table_status = models.CharField(max_length=200, null=True, blank=True, choices=TABLESTATUS, default='Reserved')
    date = models.DateTimeField(null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)  # ✅ Add this

    def __str__(self):
        orders = self.normalreservationorder_set.all()
        dish_names = ", ".join(str(order.dish) for order in orders)
        return f"{self.fullname} - {dish_names} - {self.table_status}"
    
class NormalReservationOrder(models.Model):
    reservation = models.ForeignKey(NormalReservationTable, on_delete=models.CASCADE)
    dish = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.reservation.fullname} - {self.dish.dish_name} x {self.quantity}"    

class SessionDishHistory(models.Model):
    session_key = models.CharField(max_length=255)
    dish = models.ForeignKey(Menu, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_key} - {self.dish.dish_name}"

class UnavailableDateTime(models.Model):
    date = models.DateField(unique=True, null=True)
    start_time = models.TimeField(unique=True, null=True)
    end_time = models.TimeField(unique=True, null=True)
    reason = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.date} | {self.start_time} to {self.end_time} — {self.reason or 'Unavailable'}"