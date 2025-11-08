import json

from rest_framework import serializers
from rest_framework import exceptions
from dataclasses import asdict
from modules.graph_lang.framework.parser import Parser
from modules.graph_lang.framework.validator import Validator

from modules.graph_lang.models import Graph


class GraphValidationError(BaseException):
    errors: list[dict]

    def __init__(self, errors, *args):
        super().__init__(*args)
        self.errors = errors


class GraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graph
        fields = ["id", "name", "raw_graph_data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = Parser()
        self.validator = Validator()

        # Idk czy to jest 'czyste'
        self.fields["id"].read_only = True

    def validate(self, attrs):
        graph_data = self.parser.parse(attrs["raw_graph_data"])

        if not graph_data:
            raise serializers.ValidationError(
                "Failed to parse graph", code="parse_error"
            )
        errors = self.validator.validate(graph_data)
        if errors:
            errors = [json.dumps(asdict(e)) for e in errors]

            raise serializers.ValidationError(errors, code="validation_error")

        attrs["graph_data"] = graph_data
        return attrs

    def create(self, validated_data):
        investor = validated_data["investor"]
        return Graph.objects.create(
            investor=investor,
            name=validated_data["name"],
            raw_graph_data=validated_data["raw_graph_data"],
            graph_data=validated_data["graph_data"].model_dump(),
        )


class GraphUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graph
        fields = ["id", "name", "raw_graph_data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parser = Parser()
        self.validator = Validator()

        # Idk czy to jest czyste
        self.fields["id"].read_only = True
        for field in self.fields.values():
            field.required = False

    def validate(self, attrs):
        if "raw_graph_data" in attrs:
            graph_data = self.parser.parse(attrs["raw_graph_data"])

            if not graph_data:
                raise serializers.ValidationError(
                    "Failed to parse graph", code="parse_error"
                )
            errors = self.validator.validate(graph_data)
            if errors:
                errors = [json.dumps(asdict(e)) for e in errors]

                raise serializers.ValidationError(errors, code="validation_error")

            attrs["graph_data"] = graph_data
        return attrs

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.raw_graph_data = validated_data.get(
            "raw_graph_data", instance.raw_graph_data
        )
        if "graph_data" in validated_data:
            instance.graph_data = validated_data["graph_data"].model_dump()
        instance.save()
        return instance

class PriceTimestampSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=30, decimal_places=15)
    timestamp = serializers.DateTimeField()

class TickerPrices(serializers.Serializer):
    ticker = serializers.CharField()
    prices = PriceTimestampSerializer(many=True)

class RunGraphSerializer(serializers.ModelSerializer):
    time_at = serializers.DateTimeField(required=False)
    prices = TickerPrices(many=True, required = False)

    class Meta:
        model = Graph
        fields = ['pk', 'time_at', 'prices']

class GraphResultSerializer(serializers.Serializer):
    action = serializers.JSONField()

class RunGraphResultSerializer(serializers.Serializer):
    results = GraphResultSerializer(many=True)