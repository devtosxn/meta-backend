from rest_framework.serializers import ModelSerializer
from .models import SignUpEmail


class SignUpEmailSerializer(ModelSerializer):

    class Meta:
        model = SignUpEmail

        fields = '__all__'