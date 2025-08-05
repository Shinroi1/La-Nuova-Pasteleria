from django import forms
from django.utils import timezone
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
# from django_select2.forms import Select2MultipleWidget
from django.contrib.auth.forms import UserCreationForm
from . models import Menu, NormalReservationTable, UnavailableDateTime
import json

class AdminRegisterForm(UserCreationForm):

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize or remove help texts
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        # Optional: Customize labels or widgets
        self.fields['username'].label = 'Username'
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'Enter your username'})
        self.fields['email'].widget = forms.EmailInput(attrs={'placeholder': 'Enter your email'})

        class Meta:
            model = User
            fields = ('username', 
                    'email', 
                    'first_name', 
                    'last_name',
                    'password1', 
                    'password2'
                    )
            
class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']          
               
class MenuForm(forms.ModelForm):
    dish_name = forms.CharField(
        required=True,
        max_length=65
        )
    
    category = forms.CharField(
        required=True, 
        max_length=65
        )
    
    sub_category = forms.CharField(
        required=True, 
        max_length=65
        )
    
    ingredients = forms.CharField(
        required=True, 
        max_length=200
        )
    
    price = forms.DecimalField(
        required=True, 
        decimal_places=2, 
        max_digits=10
        )
    
    image = forms.CharField(
        max_length=255,
        # choices=IMAGE_CHOICES,
        required=False
    )

    slug = forms.SlugField(
        required=False
        )
        
    class Meta:
        model = Menu
        fields = ('dish_name', 
                  'category', 
                  'sub_category',
                  'ingredients', 
                  'price',
                  'image',
                  'slug'
                  )
        
class NormalReservationForm(forms.ModelForm):
    
    fullname = forms.CharField(
        max_length= 200, 
        required=True
        )
    
    email = forms.EmailField(
        max_length= 200, 
        required=True
        )
    
    phone = forms.CharField(
        max_length= 11,
        required=True
        )
          
    party_size = forms.IntegerField(
        required=True, 
        validators=[MinValueValidator(1), MaxValueValidator(12)], 
        help_text="Maximum of 12 party size"
        )
    
    selected_dishes = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
            
    total_price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False
        )    
    
    table_status = forms.ChoiceField(
        choices= NormalReservationTable.TABLESTATUS, 
        required= False
        )
    
    date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
        )
    
    def clean(self):
        cleaned_data = super().clean()
        selected_dishes_json = cleaned_data.get('selected_dishes')

        # Calculate total price if dishes are selected
        if selected_dishes_json:
            try:
                # Ensure the parsed JSON is a list of dictionaries
                selected_dishes = json.loads(selected_dishes_json)
                print(selected_dishes)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Error decoding selected dishes data: {e}")

            total_price = 0
            dish_ids = []
            quantities = {}

            # Iterate through each item in the list
            for dish_id_str, dish_data in selected_dishes.items():
                try:
                    # Access dishId and quantity correctly as keys in the dictionary
                    dish_id = int(dish_id_str)
                    quantity = int(dish_data['quantity'])
                except (KeyError, ValueError) as e:
                    raise ValidationError(f"Invalid dish data format: {e}")

                if quantity <= 0:
                    raise ValidationError("Quantity must be greater than 0.")

                dish_ids.append(dish_id)
                quantities[dish_id] = quantity

                # Get the dish price from the database
                try:
                    dish = Menu.objects.get(id=dish_id)
                except Menu.DoesNotExist:
                    raise ValidationError(f"Dish with ID {dish_id} does not exist.")

                total_price += dish.price * quantity

            # Add total price and other data to cleaned_data
            cleaned_data['total_price'] = total_price
            cleaned_data['dish_ids'] = dish_ids
            cleaned_data['quantities'] = quantities

        else:
            # If no dishes are selected, set defaults
            cleaned_data['total_price'] = 0
            cleaned_data['dish_ids'] = []
            cleaned_data['quantities'] = {}

        return cleaned_data

    class Meta:
        model = NormalReservationTable
        fields = ('fullname',
                  'email',
                  'phone',  
                  'party_size', 
                  'selected_dishes',
                  'table_status', 
                  'total_price',
                  'date'
                  )

TIMESLOT_CHOIES = [
    ("15:00-18:00", "3:00 PM - 6:00 PM"),
    ("18:00-21:00", "6:00 PM - 9:00 PM"),
    ("custom", "Custom Time Range"),
]

class UnavailableDateTimeForm(forms.ModelForm):
    predefined_slot = forms.ChoiceField(
        choices = TIMESLOT_CHOIES,
        required= False,
        widget=forms.Select(attrs={
            'class': 'form-select', ''
            'onchange': 'toggleCustomTime(this.value)'
        })
    )

    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time', 'class': 'form-control', 'id': 'start_time_field'
        })
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time', 'class': 'form-control', 'id': 'end_time_field'
        })
    )

    class Meta:
            model = UnavailableDateTime
            fields = ['date', 'predefined_slot', 'start_time', 'end_time', 'reason']
            widgets = {
                'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
                'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'start_time_field'}),
                'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'end_time_field'}),
                'reason': forms.TextInput(attrs={'class': 'form-control'}),
            }

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get("predefined_slot")
        if slot and slot != "custom":
            try:
                start_str, end_str = slot.split('-')
                cleaned_data['start_time'] = start_str
                cleaned_data['end_time'] = end_str
            except ValueError:
                raise forms.ValidationError("Invalid predefined slot format.")
        else:
            start_time = cleaned_data.get("start_time")
            end_time = cleaned_data.get("end_time")
            if not start_time or not end_time:
                raise forms.ValidationError("Start and end time are required for custom slot.")
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")

        return cleaned_data