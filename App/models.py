from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

import uuid
# Create your models here
from django.db.models import Sum

def validateforNumeric(number):
    if not number.isdigit():
        raise ValidationError("This field can be only numbers.")

def validateforText(number):
    if (number.isdigit()):
        raise ValidationError("This field can not be only numbers.")

class Total(models.Model):

    def __str__(self):
        # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
        # total = models.IntegerField(validators=[MinValueValidator(0)])
        # Calculate sum of all related records
        salary_sum = self.salary_set.all().aggregate(total=Sum('salary'))['total'] or 0
        saving_sum = self.saving_set.all().aggregate(total=Sum('saving'))['total'] or 0
        others_sum = self.others_set.all().aggregate(total=Sum('balance'))['total'] or 0
        # When you run:
        #
        # self.salary_set.aggregate(total=Sum('salary'))
        #
        # It returns a dictionary:
        # {'total': 5000}  # The sum is stored under key 'total'
        # The key 'total' is the name you gave it in the aggregate function
        #
        # It has nothing to do with your model field named total
        
        calculated_total = salary_sum + saving_sum + others_sum
        return f"Total balance is: {calculated_total}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('Total', args=[str(self.uuid)]) # 'total' is the name from the App/urls.py under path.

class Salary(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    salary = models.IntegerField(validators=[MinValueValidator(0)])
    total = models.ForeignKey(Total, on_delete=models.CASCADE)
    def __str__(self):
            return f"Salary is: {self.salary}"
    def get_absolute_url(self):
            from django.urls import reverse
            return reverse('Salary', args=[str(self.uuid)]) # 'salary' is the name from the App/urls.py under path.

class Saving(models.Model):
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    saving = models.IntegerField(validators=[MinValueValidator(0)])
    total = models.ForeignKey(Total, on_delete=models.CASCADE)

    def __str__(self):
        return f"Saving is: {self.saving}"
    def get_absolute_url(self):
            from django.urls import reverse
            return reverse('Saving', args=[str(self.uuid)]) # 'saving' is the name from the App/urls.py under path.


class Others(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    others = models.CharField(max_length=32, validators=[validateforText])
    balance = models.IntegerField(validators=[MinValueValidator(0)])
    total = models.ForeignKey(Total, on_delete=models.CASCADE)

    def __str__(self):
        return f"Balance for {self.others} is: {self.balance}"
    def get_absolute_url(self):
            from django.urls import reverse
            return reverse('Others', args=[str(self.uuid)]) # 'others' is the name from the App/urls.py under path.




                            
