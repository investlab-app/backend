from rest_framework import serializers


class DecimalField(serializers.DecimalField):
    def __init__(self, max_digits=30, decimal_places=15, *args, **kwargs):
        super().__init__(max_digits, decimal_places, *args, **kwargs)
