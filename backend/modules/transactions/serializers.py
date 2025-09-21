from rest_framework import serializers

from modules.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    volume_sold = serializers.DecimalField(max_digits=15, decimal_places=2)
    sold_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    gain = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage_gain = serializers.FloatField()

    class Meta:
        model = Transaction
        fields = [
            "ticker",
            "transaction_time",
            "volume",
            "transaction_price",
            "current_price",
            "volume_sold",
            "sold_price",
            "gain",
            "percentage_gain",
        ]
