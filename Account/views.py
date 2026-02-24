from django.shortcuts import render

# Create your views here.

from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from .forms import CustomSignupForm


# SIGNUP VIEW
def signup(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! Please login.")
            return redirect("Account:login")
    else:
        form = CustomSignupForm()
    return render(request, "Account/signup.html", {"form": form})


# LOGIN VIEW (NOW HANDLES BY DJANGO'S OWN AUTH)
# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username',' ')
#         password = request.POST.get('password',' ')
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('Bank:Totals')
#         else:
#             messages.error(request, 'Invalid credentials')
#     return render(request, 'account/login.html')


# LOGOUT VIEW
def logout_view(request):
    logout(request)
    return redirect("Account:login")


# PROTECTED PROFILE VIEW
# @login_required
# def profile(request):
#     return render(request, 'account/profile.html', {'user': request.user})
