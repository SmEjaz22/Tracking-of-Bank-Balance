# # from uuid import FieldsType
# from django.shortcuts import render, redirect
#
#
# # Create your views here.
#
# from .models import Total, Salary, Saving, Others
# from .forms import InputSalary, InputSaving, InputOthers
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
#
# # import uuid
# from django.shortcuts import get_object_or_404
#
#
# # @login_required
# def dashboard(request):
#     if request.user.is_authenticated:
#         total, created = Total.objects.get_or_create(user=request.user)
#         uuid = total.uuid
#         context = {"uuid": uuid}
#     else:
#         context = {"uuid": None}
#     return render(request, "App/dashbaord.html", context)
#
#
# @login_required
# def get_total(request, uuid):
#
#     total_record = get_object_or_404(Total, uuid=uuid, user=request.user)
#     # totals = Total.objects.get(user = request.user)
#
#     # Get all related records
#     salaries = Salary.objects.filter(total=total_record).first()
#     savings = Saving.objects.filter(total=total_record).first()
#     others = Others.objects.filter(total=total_record).first()
#
#     # total_balance = total_record.__str__()  # This calls the __str__ method
#
#     context = {
#         "total_record": total_record,
#         "salaries": salaries,
#         "savings": savings,
#         "others": others,
#         # 'total_balance': total_balance,
#     }
#
#     # context = {
#     #     "totals": totals
#     # }
#     return render(request, "App/home.html", context)
#
#
# @login_required
# def change_salary(request, uuid):
#     total = Total.objects.get(user=request.user, uuid=uuid)
#     salary = Salary.objects.filter(total=total).first()
#
#     if request.method != "POST":
#         form = InputSalary(instance=salary)
#     else:
#         form = InputSalary(request.POST, instance=salary)
#         if form.is_valid():
#             salary = form.save(commit=False)
#             salary.total = total  # Set the total here
#             salary.save()
#             return redirect("Bank:Totals", uuid=uuid)
#
#     # context = {'salary':salary}
#     return render(request, "App/change_salary.html", {"form": form})
#
#
# @login_required
# def change_saving(request, uuid):
#     total = Total.objects.get(user=request.user, uuid=uuid)
#     saving = Saving.objects.filter(total=total).first()
#
#     if request.method != "POST":
#         form = InputSaving(instance=saving)
#     else:
#         form = InputSaving(request.POST, instance=saving)
#         if form.is_valid():
#             saving = form.save(commit=False)
#             saving.total = total  # Set the total here
#             saving.save()
#             return redirect("Bank:Totals", uuid=uuid)
#
#     # context = {'salary':salary}
#     return render(request, "App/change_saving.html", {"form": form})
#
#
# @login_required
# def change_others(request, uuid):
#     total = Total.objects.get(user=request.user, uuid=uuid)
#     others = Others.objects.filter(total=total).first()
#
#     if request.method != "POST":
#         form = InputOthers(instance=others)
#     else:
#         form = InputOthers(request.POST, instance=others)
#         if form.is_valid():
#             others = form.save(commit=False)
#             others.total = total  # Set the total here
#             others.save()
#             return redirect("Bank:Totals", uuid=uuid)
#
#     # context = {'salary':salary}
#     return render(request, "App/change_others.html", {"form": form})
