from dataclasses import asdict
from datetime import datetime

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.graph_lang.framework.price_provider import MockPriceProvider
from modules.graph_lang.framework.runner import Runner
from modules.graph_lang.models import Graph, GraphEffect
from modules.graph_lang.serializers import (
    GraphEffectSerializer,
    GraphSerializer,
    GraphUpdateSerializer,
    RunGraphResultSerializer,
    RunGraphSerializer,
)
from modules.investors.models import Investor


@extend_schema(request=GraphSerializer, responses=GraphSerializer)
class ListCreateGraphView(generics.ListCreateAPIView):
    serializer_class = GraphSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Graph.objects.filter(investor=investor)

    def perform_create(self, serializer):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        serializer.save(investor=investor)


@extend_schema(request=GraphUpdateSerializer, responses=GraphSerializer)
class RetrieveUpdateDestroyGraphView(generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
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


@extend_schema(request=RunGraphSerializer, responses=RunGraphResultSerializer)
class RunGraphView(APIView):
    def post(self, request, pk):
        get_object_or_404(Graph, pk=pk)

        input_serializer = RunGraphSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data

        price_provider = None
        time_at = datetime.now()
        if "time_at" in data and "prices" in data:
            price_provider = MockPriceProvider()
            time_at = data["time_at"]
            for ticker_prices in data["prices"]:
                ticker = ticker_prices["ticker"]
                prices = [
                    (price_point["timestamp"], price_point["price"])
                    for price_point in ticker_prices["prices"]
                ]
                price_provider.set_prices(ticker, prices)

        runner = Runner()
        effects = runner.run(
            pk,
            time_at=time_at,
            price_provider=price_provider,  # ty: ignore[invalid-argument-type]
        )

        actions = [{"action": asdict(effect)} for effect in effects]

        output_serializer = RunGraphResultSerializer({"results": actions})
        return Response(output_serializer.data)


class GraphResultView(generics.ListAPIView):
    serializer_class = GraphEffectSerializer

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        print(self.request.query_params)
        print(pk)
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        print(investor)
        graph = get_object_or_404(Graph, investor=investor, pk=pk)
        print(graph)
        return GraphEffect.objects.filter(graph=graph)
