from rest_framework import serializers

from modules.investors.models import Investor
from modules.users.models import User


class InvestorSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    watching_instruments_count = serializers.IntegerField(
        source="watching_instruments.count", read_only=True
    )

    class Meta:
        model = Investor
        fields = [
            "id",
            "user",
            "user_email",
            "user_first_name",
            "user_last_name",
            "watching_instruments",
            "watching_instruments_count",
        ]
        read_only_fields = ["id"]


class InvestorCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(write_only=True)

    class Meta:
        model = Investor
        fields = ["user_id", "watching_instruments"]

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            # Check if investor already exists for this user
            if Investor.objects.filter(user=user).exists():
                raise serializers.ValidationError(
                    "Investor already exists for this user."
                )
            return value
        except User.DoesNotExist as e:
            raise serializers.ValidationError("User does not exist.") from e

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        user = User.objects.get(id=user_id)
        investor = Investor.objects.create(user=user, **validated_data)
        return investor


class InvestorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = ["watching_instruments"]


class InvestorListQueryParams(serializers.Serializer):
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text="Page number for pagination.",
    )
    page_size = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
        help_text="Number of items per page (max 100).",
    )
    search = serializers.CharField(
        required=False,
        help_text="Search by user email, first name, or last name.",
    )


class InvestorStatsSerializer(serializers.Serializer):
    """Serializer for investor statistics data."""

    todays_return = serializers.FloatField(help_text="Today's return in currency")
    total_return = serializers.FloatField(help_text="Total return in currency")
    invested = serializers.FloatField(help_text="Total amount invested")
    total_value = serializers.FloatField(help_text="Total account value")


class AccountValueDataSerializer(serializers.Serializer):
    """Serializer for individual account value data point."""

    date = serializers.DateField(help_text="Date of the value measurement")
    value = serializers.FloatField(help_text="Account value on this date")


class AccountValueOverTimeSerializer(serializers.Serializer):
    """Serializer for account value over time data."""

    data = AccountValueDataSerializer(
        many=True, help_text="List of account value data points"
    )


class CurrentAccountValueSerializer(serializers.Serializer):
    value = serializers.FloatField()
