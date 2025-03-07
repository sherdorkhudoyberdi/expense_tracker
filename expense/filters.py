import django_filters
from .models import Transaction

class TransactionFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    to_date = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    category = django_filters.NumberFilter(field_name="category__id")
    money_account = django_filters.NumberFilter(field_name="money_account__id")

    class Meta:
        model = Transaction
        fields = ['from_date', 'to_date', 'category', 'money_account']
