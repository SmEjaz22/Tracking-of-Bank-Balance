from django import forms
from .models import Salary, Saving, Others
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class InputSalary(forms.ModelForm):
    class Meta:
        model = Salary
        fields = '__all__'
        exclude = ['total']
    # No need for overriding the save method ig.
    # salary=forms.IntegerField(validators=[MinValueValidator(0)])
    # def save(commit=True):

class InputSaving(forms.ModelForm):
    class Meta:
        model = Saving
        fields = '__all__'
        exclude = ['total']

class InputOthers(forms.ModelForm):
    class Meta:
        model = Others
        fields = '__all__'
        exclude = ['total']

