from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import MoneyAccount, Category, Transaction
from .serializers import MoneyAccountSerializer, CategorySerializer, TransactionSerializer

class MoneyAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """Retrieve all accounts or a single account based on pk."""
        if pk:  # If pk is provided, return a specific account
            account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
            serializer = MoneyAccountSerializer(account)
        else:  # If no pk, return all accounts
            accounts = MoneyAccount.objects.filter(user=request.user)
            serializer = MoneyAccountSerializer(accounts, many=True)

        return Response(serializer.data)

    def post(self, request):
        """Create a new money account and associate it with the authenticated user."""
        serializer = MoneyAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Set user automatically
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """Update an existing money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        serializer = MoneyAccountSerializer(account, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partially update a money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        serializer = MoneyAccountSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete a money account (only if owned by the user)."""
        account = get_object_or_404(MoneyAccount, pk=pk, user=request.user)
        account.delete()
        return Response({"message": "Account deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()  # All users can view categories
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class AdminCategoryView(APIView):
    permission_classes = [IsAdminUser]  # Only admin can create categories

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.validated_data['category']
            transaction_type = serializer.validated_data['transaction_type']

            if category.category_type != transaction_type:
                return Response({'error': 'Category type must match transaction type'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
