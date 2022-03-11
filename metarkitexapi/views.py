from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import status
from .models import SignUpEmail
from . import serializers

# Create your views here.

class EmailViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.SignUpEmailSerializer

    def add_user_email(self, request):
        data = request.data
        mail_serializer = serializers.SignUpEmailSerializer(data=request.data)

        if mail_serializer.is_valid():
            mail_serializer.save()
            return Response(mail_serializer.data, status=status.HTTP_201_CREATED)
        return Response(mail_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
