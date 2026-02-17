from django.shortcuts import render


# Create your views here.

from .models import Total, Salary, Saving, Others
from .forms import InputSalary

def get_total(request):
    totals = Total.objects.all()
    context = {
        "totals": totals
    }
    return render(request, 'App/home.html', context)


def update_salary(request):

    salary = Salary.objects.first()
    if request.method!='POST':
        form=InputSalary(salary)
    else:
        form=InputSalary(request.POST)
        if form.is_valid():
            updated_salary = form.save(commit=False)
            updated_salary = request.user
            updated_salary.save()
            form.save()


    salary = Salary.objects.first()
    form  = InputSalary(salary)
    # context = {'salary':salary}
    # return render (request, 'App/home.html', context)


