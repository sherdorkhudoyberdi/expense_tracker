from django.db.models import Q
from django.db.models import Sum
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from .filters import TransactionFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import MoneyAccount, Category, Transaction, HiddenCategory
from .serializers import MoneyAccountSerializer, CategorySerializer, TransactionSerializer

class MoneyAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: MoneyAccountSerializer(many=True)}
    )
    def get(self, request, pk=None):
        """Retrieve all accounts or a single account based on pk."""
        if pk:  # If pk is provided, return a specific account
            account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
            serializer = MoneyAccountSerializer(account)
        else:  # If no pk, return all accounts
            accounts = MoneyAccount.objects.filter(user=request.user)
            serializer = MoneyAccountSerializer(accounts, many=True)

        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=MoneyAccountSerializer,
        responses={201: MoneyAccountSerializer()}
    )
    def post(self, request):
        """Create a new money account and associate it with the authenticated user."""
        serializer = MoneyAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Set user automatically
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=MoneyAccountSerializer,
        responses={200: MoneyAccountSerializer()}
    )
    def put(self, request, pk):
        """Update an existing money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        serializer = MoneyAccountSerializer(account, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=MoneyAccountSerializer,
        responses={200: MoneyAccountSerializer()}
    )
    def patch(self, request, pk):
        """Partially update a money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        serializer = MoneyAccountSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={204: "Account deleted successfully"}
    )
    def delete(self, request, pk):
        """Delete a money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        account.delete()
        return Response({"message": "Account deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request):
        """
        Users see:
        - All categories created by admin (user=None) that are NOT hidden for them
        - Their own categories
        """
        hidden_categories = HiddenCategory.objects.filter(user=request.user).values_list('category', flat=True)
        categories = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True)).exclude(id__in=hidden_categories)

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CategorySerializer,
        responses={201: CategorySerializer()}
    )
    def post(self, request):
        """
        Users can create personal categories.
        """
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Save with logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            204: openapi.Response(description="Category deleted successfully"),
            200: openapi.Response(description="Admin category hidden for user"),
            403: openapi.Response(description="You do not have permission to delete this category"),
            404: openapi.Response(description="Category not found"),
        }
    )

    def delete(self, request, pk):
        """
        Users can delete:
        - Their own categories (deleted completely)
        - Admin-created categories (only hidden for themselves)
        """
        category = get_object_or_404(Category, pk=pk)

        if category.user == request.user:
            category.delete()
            return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        elif category.user is None:
            # Hide admin-created category for this user
            HiddenCategory.objects.get_or_create(user=request.user, category=category)
            return Response({"message": "Admin category hidden for user"}, status=status.HTTP_200_OK)

        return Response({"error": "You do not have permission to delete this category"},
                        status=status.HTTP_403_FORBIDDEN)


class AdminCategoryView(APIView):
    permission_classes = [IsAdminUser]  # Only admin can create categories

    @swagger_auto_schema(
        request_body=CategorySerializer,
        responses={
            201: CategorySerializer(),
            400: openapi.Response(description="Invalid request data"),
        }
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionPagination(PageNumberPagination):
    page_size = 10  # Set the number of transactions per page
    page_size_query_param = 'page_size'  # Allow users to specify page size
    max_page_size = 100  # Prevent excessively large responses

class TransactionView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['date']  # Allow ordering by date

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('from_date', openapi.IN_QUERY, description="Filter by start date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('to_date', openapi.IN_QUERY, description="Filter by end date (YYYY-MM-DD)",
                              type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('money_account', openapi.IN_QUERY, description="Filter by money account ID",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number for pagination",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of items per page",
                              type=openapi.TYPE_INTEGER),
        ],
        responses={200: TransactionSerializer(many=True)}
    )
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')

        # Apply filtering using django-filter
        filtered_transactions = TransactionFilter(request.GET, queryset=transactions).qs

        # Paginate results
        paginator = TransactionPagination()
        paginated_transactions = paginator.paginate_queryset(filtered_transactions, request)
        serializer = TransactionSerializer(paginated_transactions, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['category', 'transaction_type', 'amount', 'money_account'],
            properties={
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description="Category ID"),
                'transaction_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['income', 'expense'],
                                                   description="Type of transaction"),
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                         description="Transaction amount"),
                'money_account': openapi.Schema(type=openapi.TYPE_INTEGER, description="Money Account ID"),
                'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE,
                                       description="Transaction date (optional)")
            },
        ),
        responses={201: TransactionSerializer()}
    )
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.validated_data['category']
            transaction_type = serializer.validated_data['transaction_type']

            if category.category_type != transaction_type:
                return Response({'error': 'Category type must match transaction type'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer()}
    )
    def put(self, request, pk):
        """
        Fully update an existing transaction and adjust the balance accordingly.
        """
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        money_account = transaction.money_account
        old_amount = transaction.amount
        old_type = transaction.transaction_type

        serializer = TransactionSerializer(transaction, data=request.data, partial=False)
        if serializer.is_valid():
            new_type = serializer.validated_data.get('transaction_type', old_type)
            new_amount = serializer.validated_data.get('amount', old_amount)
            new_money_account = serializer.validated_data.get('money_account', money_account)

            # Reverse the previous transaction effect
            if old_type == 'income':
                money_account.balance -= old_amount
            elif old_type == 'expense':
                money_account.balance += old_amount

            # Apply the new transaction effect
            if new_type == 'income':
                new_money_account.balance += new_amount
            elif new_type == 'expense':
                if new_money_account.balance < new_amount:
                    return Response({'error': 'Insufficient balance for this expense'}, status=status.HTTP_400_BAD_REQUEST)
                new_money_account.balance -= new_amount

            # Save changes
            if new_money_account != money_account:
                money_account.save()  # Save old account balance if changed
            new_money_account.save()
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer()}
    )
    def patch(self, request, pk):
        """
        Partially update a transaction and adjust the balance accordingly.
        """
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        money_account = transaction.money_account
        old_amount = transaction.amount
        old_type = transaction.transaction_type

        serializer = TransactionSerializer(transaction, data=request.data, partial=True)
        if serializer.is_valid():
            new_type = serializer.validated_data.get('transaction_type', old_type)
            new_amount = serializer.validated_data.get('amount', old_amount)
            new_money_account = serializer.validated_data.get('money_account', money_account)

            # Reverse the previous transaction effect
            if old_type == 'income':
                money_account.balance -= old_amount
            elif old_type == 'expense':
                money_account.balance += old_amount

            # Apply the new transaction effect
            if new_type == 'income':
                new_money_account.balance += new_amount
            elif new_type == 'expense':
                if new_money_account.balance < new_amount:
                    return Response({'error': 'Insufficient balance for this expense'}, status=status.HTTP_400_BAD_REQUEST)
                new_money_account.balance -= new_amount

            # Save changes
            if new_money_account != money_account:
                money_account.save()  # Save old account balance if changed
            new_money_account.save()
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={204: "Transaction deleted successfully"})
    def delete(self, request, pk):
        """
        Delete a transaction and adjust the MoneyAccount balance accordingly.
        """
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        money_account = transaction.money_account

        # Reverse the transaction before deleting
        if transaction.transaction_type == 'income':
            money_account.balance -= transaction.amount  # Remove added income
        elif transaction.transaction_type == 'expense':
            money_account.balance += transaction.amount  # Restore deducted expense

        money_account.save()  # Save the updated balance
        transaction.delete()

        return Response({"message": "Transaction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class MonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('year', openapi.IN_PATH, description="Year (YYYY)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('month', openapi.IN_PATH, description="Month (1-12)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "year": openapi.Schema(type=openapi.TYPE_INTEGER, description="Requested year"),
                    "month": openapi.Schema(type=openapi.TYPE_INTEGER, description="Requested month"),
                    "total_income": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                                   description="Total income for the month"),
                    "total_expense": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                                    description="Total expense for the month"),
                    "balance": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                              description="Net balance (income - expenses)"),
                }
            ),
            400: "Invalid request parameters",
            403: "Unauthorized",
        }
    )

    def get(self, request, year, month):
        """
        Returns total income, total expenses, and net balance for a given month.
        """
        transactions = Transaction.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        )

        total_income = transactions.filter(transaction_type="income").aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = transactions.filter(transaction_type="expense").aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_income - total_expense

        return Response({
            "year": year,
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance
        })


class CategorySpendingView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('year', openapi.IN_PATH, description="Year (YYYY)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('month', openapi.IN_PATH, description="Month (1-12)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "year": openapi.Schema(type=openapi.TYPE_INTEGER, description="Requested year"),
                    "month": openapi.Schema(type=openapi.TYPE_INTEGER, description="Requested month"),
                    "total_expense": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                                    description="Total expenses for the month"),
                    "categories": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "category": openapi.Schema(type=openapi.TYPE_STRING, description="Category name"),
                                "total_spent": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL,
                                                              description="Total amount spent in this category"),
                                "percentage": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT,
                                                             description="Percentage of total expenses")
                            }
                        )
                    )
                }
            ),
            400: "Invalid request parameters",
            403: "Unauthorized",
        }
    )

    def get(self, request, year, month):
        """
        Returns category-wise spending and their percentage of total spending in a given month.
        """
        transactions = Transaction.objects.filter(
            user=request.user,
            transaction_type="expense",
            date__year=year,
            date__month=month
        )

        total_expense = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        category_spending = transactions.values('category__name').annotate(total=Sum('amount'))

        response_data = []
        for item in category_spending:
            category_name = item['category__name']
            category_total = item['total']
            percentage = (category_total / total_expense * 100) if total_expense > 0 else 0
            response_data.append({
                "category": category_name,
                "total_spent": category_total,
                "percentage": round(percentage, 2)
            })

        return Response({
            "year": year,
            "month": month,
            "total_expense": total_expense,
            "categories": response_data
        })