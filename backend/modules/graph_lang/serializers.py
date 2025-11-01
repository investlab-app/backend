import json

from rest_framework import serializers
from rest_framework import exceptions
from dataclasses import asdict
from modules.graph_lang.framework.parser import Parser
from modules.graph_lang.framework.validator import Validator

from modules.graph_lang.models import Graph

class GraphValidationError(BaseException):
    errors :list[dict]

    def __init__(self, errors,  *args):
        super().__init__(*args)
        self.errors = errors

class GraphSerializer(serializers.ModelSerializer):
    graph_data = serializers.JSONField(read_only=True)

    class Meta:
        model = Graph
        fields = [
            'raw_graph_data',
            'graph_data'
        ]

    def validate(self, attrs):
        parser = Parser()
        validator = Validator()
        graph_data = parser.parse(attrs['raw_graph_data'])

        if not graph_data:
            raise serializers.ValidationError('Failed to parse graph', code='parse_error')
        errors = validator.validate(graph_data)
        if errors:
            errors = [
                json.dumps(asdict(e))
                for e in errors
            ]

            raise serializers.ValidationError(errors, code='validation_error')

        attrs['graph_data'] = graph_data
        return attrs

    def create(self, validated_data):
        investor = validated_data['investor']
        return Graph.objects.create(
            investor=investor,
            raw_graph_data=validated_data['raw_graph_data'],
            graph_data=json.dumps(validated_data['graph_data'])
        )

    def update(self, instance, validated_data):
        instance.raw_graph_data=validated_data['raw_graph_data']
        instance.graph_data=json.dumps(validated_data['graph_data'])
        instance.save()
        return instance


