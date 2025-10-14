import logging

from rest_framework import generics
from rest_framework.response import Response

from config.settings import VAPID_PUBLIC_KEY

logger = logging.getLogger(__name__)




class VapidPublicKeyView(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        return Response({"public_key": VAPID_PUBLIC_KEY})
