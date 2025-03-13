from rest_framework import serializers
from .models import MoneyAccount, Category, Transaction

class MoneyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneyAccount
        fields = ['id', 'user', 'name', 'account_type', 'currency', 'balance']
        read_only_fields = ['user']

    def create(self, validated_data):
        """
        Allow users to set an initial balance when creating an account.
        """
        initial_balance = validated_data.pop('balance', 0.00)
        account = MoneyAccount.objects.create(**validated_data)
        account.balance = initial_balance
        account.save()
        return account

    # def update(self, instance, validated_data):
    #     """
    #     Update all fields, but reset balance to zero before setting a new balance.
    #     """
    #     new_balance = validated_data.get("balance", instance.balance)
    #
    #     # Reset balance to zero and then set the new balance
    #     instance.balance = 0
    #     instance.balance += new_balance  # Ensure balance is updated correctly
    #
    #     # Update all other fields dynamically
    #     for attr, value in validated_data.items():
    #         if attr != "balance":  # Avoid setting balance twice
    #             setattr(instance, attr, value)
    #
    #     instance.save()
    #     return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'user']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'category', 'transaction_type', 'amount', 'money_account', 'date']
        read_only_fields = ['user']

    def create(self, validated_data):
        if 'money_account' not in validated_data:
            raise serializers.ValidationError({"money_account": "This field is required."})

        return super().create(validated_data)
