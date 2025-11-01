from rest_framework import generics
from rest_framework import exceptions
from rest_framework import status
from rest_framework.response import Response
import json


from modules.graph_lang.models import Graph
from modules.investors.models import Investor
from modules.graph_lang.framework.parser import Parser
from modules.graph_lang.framework.validator import Validator
from modules.graph_lang.serializers import GraphSerializer, GraphValidationError


class ListCreateGraphView(generics.ListCreateAPIView):
    serializer_class = GraphSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser = Parser()
        self.validator = Validator()

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Graph.objects.filter(investor=investor)

    def perform_create(self, serializer):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        serializer.save(investor=investor)

class RetrieveUpdateDestroyGraphView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GraphSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parser = Parser()
        self.validator = Validator()

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Graph.objects.filter(investor=investor)

    def perform_update(self, serializer):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        serializer.save(investor=investor)

    def perform_destroy(self, instance):
        instance.delete()
