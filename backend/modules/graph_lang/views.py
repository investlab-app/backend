from rest_framework import generics
from rest_framework import exceptions
from rest_framework import status
from rest_framework.response import Response
import json
from drf_spectacular.utils import extend_schema


from modules.graph_lang.models import Graph
from modules.investors.models import Investor
from modules.graph_lang.serializers import GraphSerializer, GraphUpdateSerializer


@extend_schema(
    request=GraphSerializer,
    responses=GraphSerializer
)
class ListCreateGraphView(generics.ListCreateAPIView):
    serializer_class = GraphSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Graph.objects.filter(investor=investor)

    def perform_create(self, serializer):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        serializer.save(investor=investor)


@extend_schema(
    request = GraphUpdateSerializer,
    responses = GraphSerializer
)
class RetrieveUpdateDestroyGraphView(generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GraphUpdateSerializer
        return GraphSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Graph.objects.filter(investor=investor)

    def perform_update(self, serializer):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        serializer.save(investor=investor)

    def perform_destroy(self, instance):
        instance.delete()
