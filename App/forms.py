from django import forms
from .models import Salary, Saving, Others
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

import random
import string

class InputSalary(forms.ModelForm):
    class meta:
        model = Salary
        fields = '__all__'

    Salary=forms.IntegerField(validators=[MinValueValidator(0)])
