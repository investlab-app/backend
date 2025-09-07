from rest_framework import serializers

from modules.core import defaults
from modules.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    current_price = defaults.DecimalField()
    volume_sold = serializers.IntegerField()
    sold_price = defaults.DecimalField()
    gain = defaults.DecimalField()
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
