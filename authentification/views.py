from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import OTPCode
from .serializers import EmailLoginRequestSerializer, OTPVerifySerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.conf import settings
import textwrap


User = get_user_model()

class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Rate limiting
            if OTPCode.too_many_requests(email):
                return Response({"error": "Terlalu banyak permintaan OTP dalam 10 menit. Coba lagi nanti."}, status=429)

            if not OTPCode.can_send_otp(email):
                return Response({"error": "OTP sudah dikirim. Tunggu 1 menit sebelum mencoba lagi."}, status=429)

            code = OTPCode.generate_otp()
            OTPCode.objects.create(email=email, code=code)

            message = textwrap.dedent(f"""\
                Hi {email},

                Here is your OTP code:

                    {code}

                This code is valid for 5 minutes.
                Do not share this code with anyone, including anyone claiming to be from Sparklore.

                If you did not request this code, please ignore this email.

                Thank you,
                Sparklore Team
            """)

            send_mail(
                subject="Your OTP Code – Sparklore",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({"message": "OTP dikirim ke email."}, status=200)

        return Response(serializer.errors, status=400)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            try:
                otp_obj = OTPCode.objects.filter(email=email, code=code).latest('created_at')
            except OTPCode.DoesNotExist:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            if otp_obj.is_expired():
                return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(email=email)
            if created:
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "new_user": created
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
