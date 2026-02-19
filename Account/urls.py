# HANDLING AUTH WITHOUT DJANGO'S BUILT-IN AUTH CONFIGURATION
#
# from django.urls import path
# from . import views
#
# urlpatterns = [
#     path('signup/', views.signup, name='signup'),
#     path('login/', views.login_view, name='login'),
#     path('logout/', views.logout_view, name='logout'),
#     # path('profile/', views.profile, name='profile'),
# ]


from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'Account'

urlpatterns = [
    # Use Django's built-in views
    path('login/', auth_views.LoginView.as_view(template_name='Account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Custom signup view
    path('signup/', views.signup, name='signup'),
    # path('profile/', views.profile, name='profile'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

]
