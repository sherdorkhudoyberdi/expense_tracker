from django.urls import path
from .views import (MoneyAccountView, CategoryView, TransactionView, TransactionDetailView,
                    AdminCategoryView, CategoryDetailView, MonthlySummaryView, CategorySpendingView)

urlpatterns = [
    path('categories/', CategoryView.as_view(), name='categories'),  # Users can view categories
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('admin/categories/', AdminCategoryView.as_view(), name='admin-categories'),  # Admin can create categories
    path('transactions/', TransactionView.as_view(), name='transactions'),  # Users can add transactions
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('accounts/', MoneyAccountView.as_view(), name='money-accounts'),  # Get and create accounts
    path('accounts/<int:pk>/', MoneyAccountView.as_view(), name='money-account-detail'),  # Update & delete account
    path('monthly-summary/<int:year>/<int:month>/', MonthlySummaryView.as_view(), name='monthly-summary'),
    path('category-spending/<int:year>/<int:month>/', CategorySpendingView.as_view(), name='category-spending'),
]