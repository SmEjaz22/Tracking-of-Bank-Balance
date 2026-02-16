from django.shortcuts import render


# Create your views here.

from .models import Total, Salary, Saving, Others

def get_salary(request, uuid):
    salary = Salary.objects.all()
    context = {
        "salary": salary
    }
    return render(request, 'App/home.html', context)
