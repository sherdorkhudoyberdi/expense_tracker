from django.db import models

from users.models import CustomUser

# Create your models here.


class MoneyAccount(models.Model):
    ACCOUNT_TYPES = [('cash', 'Cash'), ('credit_card', 'Credit Card')]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=10, default='USD')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100, unique=True)  # Unique category names
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPE_CHOICES)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} ({self.category_type})"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)  # Uses predefined categories
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    money_account = models.ForeignKey('MoneyAccount', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.money_account:
            raise ValueError("Money Account is required for the transaction.")

        if self.transaction_type == 'income':
            self.money_account.balance += self.amount
        elif self.transaction_type == 'expense':
            if self.money_account.balance < self.amount:
                raise ValueError("Insufficient balance for this expense.")
            self.money_account.balance -= self.amount

        self.money_account.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.amount} - {self.category.name} ({self.transaction_type})"