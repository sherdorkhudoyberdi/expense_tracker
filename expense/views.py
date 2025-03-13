from django.db.models import Q
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
        Fully update an existing transaction.
        """
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        serializer = TransactionSerializer(transaction, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer()}
    )
    def patch(self, request, pk):
        """
        Partially update a transaction.
        """
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        serializer = TransactionSerializer(transaction, data=request.data, partial=True)
        if serializer.is_valid():
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