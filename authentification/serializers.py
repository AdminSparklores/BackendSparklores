from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTPCode

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class FullUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__' 

class EmailLoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4)

    def validate_code(self, value):
        try:
            otp = OTPCode.objects.get(code=value)
            if otp.is_expired():
                raise serializers.ValidationError("OTP code has expired.")
        except OTPCode.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP code.")
        return value