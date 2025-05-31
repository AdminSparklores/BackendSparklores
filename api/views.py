from datetime import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Charm, DiscountCampaign, GiftSetOrBundleMonthlySpecial, NewsletterSubscriber, PhotoGallery, Review, Product, Cart, CartItem, Order, VideoContent, PageBanner #Payment
from .serializers import (
    CharmSerializer, DiscountCampaignSerializer, GiftSetOrBundleMonthlySpecialProductSerializer, ProductSerializer,
    CartSerializer, CartItemSerializer,
    OrderSerializer, NewsletterSubscriberSerializer,
    ReviewSerializer, VideoContentSerializer,
    PageBannerSerializer, PhotoGalerySerializer#PaymentSerializer
)
# from .services import MidtransService, RajaOngkirService
from django.db import transaction
from django.utils import timezone

class CharmViewSet(viewsets.ModelViewSet):
    queryset = Charm.objects.all()
    serializer_class = CharmSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(cart=cart)
        if 'charms' in serializer.validated_data:
            item.charms.set(serializer.validated_data['charms'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)        

    @action(detail=True, methods=['patch'])
    def update_item(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        serializer = CartItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if 'charms' in serializer.validated_data:
            item.charms.set(serializer.validated_data['charms'])
        cart = item.cart
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        item.delete()
        cart = Cart.objects.get(user=request.user)
        return Response(CartSerializer(cart).data)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    cart = Cart.objects.prefetch_related('items__product', 'items__charms').filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return Response({'error': 'Keranjang kosong.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        total_price = 0
        for item in cart.items.all():
            # Validasi stok produk
            if item.quantity > item.product.stock:
                return Response({'error': f"Stok tidak cukup untuk produk {item.product.name}"}, status=400)

            item_total = item.product.price * item.quantity if item.product else 0
            charm_total = sum([charm.price for charm in item.charms.all()]) * item.quantity
            total_price += item_total + charm_total

            # Kurangi stok produk
            item.product.stock -= item.quantity
            item.product.sold_stok += item.quantity
            item.product.save()

        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status='pending',
            shipping_address=request.data.get('shipping_address', '-'),
            shipping_cost=request.data.get('shipping_cost', 0),
        )
        order.products.set([item.product for item in cart.items.all()])
        
        # Hapus isi keranjang
        cart.items.all().delete()

    return Response({'message': 'Checkout berhasil', 'order_id': order.id}, status=201)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def checkout(request):
#     cart = get_object_or_404(Cart, user=request.user)
#     if not cart.items.exists():
#         return Response({'error':'Cart kosong'}, status=status.HTTP_400_BAD_REQUEST)
#     with transaction.atomic():
#         total = sum((item.product.price * item.quantity) + sum(c.price for c in item.charms.all())
#                     for item in cart.items.all())
#         # estimate shipping
#         est = RajaOngkirService.estimate_cost(...)
#         shipping_cost = est['rajaongkir']['results'][0]['costs'][0]['cost'][0]['value']
#         order = Order.objects.create(
#             user=request.user, total_price=total, shipping_address=request.data['shipping_address'],
#             shipping_cost=shipping_cost
#         )
#         # Midtrans charge
#         mid = MidtransService.create_transaction(order.id, float(order.total_price+shipping_cost),
#                                                 request.data.get('payment_type','qris'))
#         Payment.objects.create(
#             order=order, transaction_id=mid['transaction_id'], method=mid['payment_type'],
#             amount=mid['gross_amount'], status=mid['transaction_status']
#         )
#         cart.items.all().delete()
#     return Response({'order_id':order.id, 'midtrans':mid})

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