from django.urls import path
from .views import RequestOTPView, VerifyOTPView, CurrentUserDetailView, UserListView

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('me/', CurrentUserDetailView.as_view(), name='user-detail'),
]