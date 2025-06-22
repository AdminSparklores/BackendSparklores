from collections import Counter
from .services import trackresi
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import CartItemCharm, Charm, DiscountCampaign, GiftSetOrBundleMonthlySpecial, NewsletterSubscriber, OrderItem, OrderItemCharm, PhotoGallery, Review, Product, Cart, CartItem, Order, VideoContent, PageBanner #Payment
from .serializers import (
    CharmSerializer, DiscountCampaignSerializer, GiftSetOrBundleMonthlySpecialProductSerializer, ProductSerializer,
    CartSerializer, CartItemSerializer,
    OrderSerializer, NewsletterSubscriberSerializer,
    ReviewSerializer, VideoContentSerializer,
    PageBannerSerializer, PhotoGalerySerializer
)
from django.db import transaction
from django.utils import timezone
import midtransclient
import os
from dotenv import load_dotenv

load_dotenv()


class CharmViewSet(viewsets.ModelViewSet):
    queryset = Charm.objects.all()
    serializer_class = CharmSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category', 'label']
    ordering_fields = ['price', 'rating']

class GiftSetOrBundleMonthlySpecialViewSet(viewsets.ModelViewSet):
    queryset = GiftSetOrBundleMonthlySpecial.objects.all()
    serializer_class = GiftSetOrBundleMonthlySpecialProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category', 'label']
    ordering_fields = ['price', 'rating']

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        charms = request.data.get('charms', [])
        request_data = request.data.copy()
        request_data['charms'] = charms 

        serializer = CartItemSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(cart=cart)

        if charms:
            if len(charms) > 5:
                return Response({'error': 'Max 5 charms per item.'}, status=400)

            item.charms.clear()
            charm_counts = Counter(charms)
            for charm_id, qty in charm_counts.items():
                charm = get_object_or_404(Charm, pk=charm_id)
                CartItemCharm.objects.create(item=item, charm=charm, quantity=qty)

        return Response(CartSerializer(cart, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_item(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        charms = request.data.get('charms', None)
        request_data = request.data.copy()

        serializer = CartItemSerializer(item, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if charms is not None:
            if len(charms) > 5:
                return Response({'error': 'Max 5 charms per item.'}, status=400)

            item.charms.clear()
            charm_counts = Counter(charms)
            for charm_id, qty in charm_counts.items():
                charm = get_object_or_404(Charm, pk=charm_id)
                CartItemCharm.objects.create(item=item, charm=charm, quantity=qty)

        return Response(CartSerializer(item.cart, context={'request': request}).data)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        item.delete()
        cart = Cart.objects.get(user=request.user)
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'])
    def selective_checkout(self, request):
        pass

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_name', 'products__name']
    ordering_fields = ['rating', 'uploaded_at']

class NewsletterSubscriberViewSet(viewsets.ModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('fulfillment_status')
        rejection_reason = request.data.get('rejection_reason', '')

        if new_status not in dict(Order.FulfillmentStatus.choices):
            return Response({'error': 'Invalid status'}, status=400)

        if new_status == Order.FulfillmentStatus.NOT_ACCEPTED and not rejection_reason:
            return Response({'error': 'Alasan penolakan wajib diisi untuk status not accepted'}, status=400)

        order.fulfillment_status = new_status
        order.rejection_reason = rejection_reason if new_status == Order.FulfillmentStatus.NOT_ACCEPTED else ''
        order.save()

        return Response({'message': f'Status updated to {new_status}'})

class VideoContentViewSet(viewsets.ModelViewSet):
    queryset = VideoContent.objects.all()
    serializer_class = VideoContentSerializer
    permission_classes = [AllowAny]

class PageBannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PageBanner.objects.all()
    serializer_class = PageBannerSerializer
    permission_classes = [AllowAny]

class PhotoGalleryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PhotoGallery.objects.all()
    serializer_class = PhotoGalerySerializer
    permission_classes = [AllowAny]

class DiscountCampaignViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiscountCampaign.objects.all()
    serializer_class = DiscountCampaignSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return DiscountCampaign.objects.all()

class MidtransSnapTokenView(APIView):
    def post(self, request):
        midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY")
        midtrans_is_production = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower()
        try:
            data = request.data
            order_id = data.get('order_id')
            gross_amount = data.get('gross_amount')
            email = data.get('email')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            phone = data.get('phone')
            address = data.get('address')
            city = data.get('city')
            postal_code = data.get('postal_code')
            country = data.get('country')
            notes = data.get('notes')
            item_details = data.get('item_details') 

            snap = midtransclient.Snap(
                is_production=midtrans_is_production,
                server_key=midtrans_server_key
            )

            param = {
                "transaction_details": {
                    "order_id": order_id,
                    "gross_amount": gross_amount
                },
                "item_details": item_details,
                "customer_details": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "billing_address": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "city": city,
                        "postal_code": postal_code,
                        "country_code": country
                    },
                    "shipping_address": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "address": address,
                        "city": city,
                        "postal_code": postal_code,
                        "country_code": country
                    }
                },
                "Notes": notes
            }

            transaction = snap.create_transaction(param)
            return Response({
                'token': transaction['token'],
                'redirect_url': transaction['redirect_url']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def direct_checkout(request):
    pass