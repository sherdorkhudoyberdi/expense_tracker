from django.contrib import admin
from .models import MoneyAccount, Transaction, Category

class MoneyAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'account_type', 'currency', 'balance')
    search_fields = ('name', 'user__username')
    list_filter = ('account_type', 'currency')

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'transaction_type', 'amount', 'money_account', 'date')
    search_fields = ('user__username', 'category__name')
    list_filter = ('transaction_type', 'category', 'date')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category_type')
    search_fields = ('name',)
    list_filter = ('category_type',)

admin.site.register(MoneyAccount, MoneyAccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Category, CategoryAdmin)
