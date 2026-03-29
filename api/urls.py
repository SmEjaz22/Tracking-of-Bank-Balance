from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/',                  views.login,                name='login'),

    # Pockets
    path('pockets/',                     views.pockets,              name='pockets'),
    path('pockets/<uuid:pk>/',           views.pocket_detail,        name='pocket-detail'),

    # Transactions
    path('transactions/',                views.transactions,         name='transactions'),
    path('transactions/<uuid:pk>/reassign/', views.reassign_transaction, name='reassign-transaction'),

    # Pattern
    path('suggest/',                     views.suggest,              name='suggest'),
    path('suggest/confirm/',             views.confirm_suggestion,   name='confirm-suggestion'),
]
