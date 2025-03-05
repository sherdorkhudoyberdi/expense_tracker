from django.urls import path
from .views import MoneyAccountView, CategoryView, TransactionView, AdminCategoryView

urlpatterns = [
    path('categories/', CategoryView.as_view(), name='categories'),  # Users can view categories
    path('admin/categories/', AdminCategoryView.as_view(), name='admin-categories'),  # Admin can create categories
    path('transactions/', TransactionView.as_view(), name='transactions'),  # Users can add transactions
    path('accounts/', MoneyAccountView.as_view(), name='money-accounts'),  # Get and create accounts
    path('accounts/<int:pk>/', MoneyAccountView.as_view(), name='money-account-detail'),  # Update & delete account
]