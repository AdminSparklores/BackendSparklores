from collections import Counter
from .services.order_service import send_order_confirmation_email, create_order
from .services.midtrans_services import create_midtrans_token
from .services.jet_service import JetService
from .services.review_service import create_and_send_review_token
from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import JNTLocation, CartItemCharm, Charm, DiscountCampaign, GiftSetOrBundleMonthlySpecial, JNTOrder, NewsletterSubscriber, OrderItem, OrderItemCharm, PhotoGallery, Review, Product, Cart, CartItem, Order, VideoContent, PageBanner, ReviewToken
from .serializers import (
    CharmSerializer, DiscountCampaignSerializer, GiftSetOrBundleMonthlySpecialProductSerializer, JNTOrderSerializer, ProductSerializer,
    CartSerializer, CartItemSerializer,
    OrderSerializer, NewsletterSubscriberSerializer,
    ReviewSerializer, VideoContentSerializer,
    PageBannerSerializer, PhotoGalerySerializer,
    OrderTableSerializer, JNTLocationSerializer
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
        request_data['charms_input'] = charms 

        serializer = CartItemSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(cart=cart)

        if charms:
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

        if charms is not None:
            request_data['charms_input'] = charms

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

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_name', 'products__name']
    ordering_fields = ['rating', 'uploaded_at']

@api_view(['GET'])
def validate_review_token(request):
    token_str = request.query_params.get('token')
    try:
        token = ReviewToken.objects.get(token=token_str)
        if not token.is_valid():
            return Response({'error': 'Token expired or used'}, status=403)
        return Response({
            'user_id': token.user.id,
            'order_id': token.order.id
        })
    except ReviewToken.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=404)

@api_view(['POST'])
def submit_review_via_token(request):
    token_str = request.data.get('token')

    try:
        token = ReviewToken.objects.get(token=token_str)
        if not token.is_valid():
            return Response({'error': 'Token expired or used'}, status=403)

        order = token.order

        # Ambil semua id yang diizinkan dari order
        allowed_products = list(order.items.filter(product__isnull=False).values_list('product_id', flat=True))
        allowed_giftsets = list(order.items.filter(gift_set__isnull=False).values_list('gift_set_id', flat=True))
        allowed_charms = list(order.items.values_list('charms__charm_id', flat=True))

        product_ids = request.data.get('products', [])
        gift_set_ids = request.data.get('gift_sets', [])
        charm_ids = request.data.get('charms', [])

        # Validasi apakah item yang dikirim benar-benar ada di order
        if not set(product_ids).issubset(set(allowed_products)):
            return Response({'error': 'Beberapa produk tidak termasuk dalam pesanan'}, status=400)
        if not set(gift_set_ids).issubset(set(allowed_giftsets)):
            return Response({'error': 'Beberapa gift set tidak termasuk dalam pesanan'}, status=400)
        if not set(charm_ids).issubset(set(allowed_charms)):
            return Response({'error': 'Beberapa charms tidak termasuk dalam pesanan'}, status=400)

        data = request.data.copy()
        data['user_name'] = token.user.username or token.user.email 
        data['user_email'] = token.user.email
        data['order'] = order.id

        serializer = ReviewSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            token.used = True
            token.save()
            return Response(ReviewSerializer(review).data, status=201)
        else:
            return Response(serializer.errors, status=400)

    except ReviewToken.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=404)

class NewsletterSubscriberViewSet(viewsets.ModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    permission_classes = [AllowAny]

class AdminOrderTableView(ListAPIView):
    serializer_class = OrderTableSerializer
    permission_classes = [AllowAny] #[IsAdminUser]
    queryset = Order.objects.all().order_by('-created_at')

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(fulfillment_status=status_filter)
        return qs

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # [IsAuthenticated] 

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            return Order.objects.filter(user=user).order_by('-created_at')
        return Order.objects.all().order_by('-created_at')

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

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_labels(self, request):
        order_ids = request.data.get("order_ids", [])
        updated = []
        with transaction.atomic():
            orders = Order.objects.filter(
                id__in=order_ids,
                fulfillment_status__in=[
                    Order.FulfillmentStatus.AWAITING_SHIPMENT,
                    Order.FulfillmentStatus.PENDING,
                ]
            )
            for order in orders:
                order.fulfillment_status = Order.FulfillmentStatus.COLLECTION
                order.save()
                updated.append(order.id)
        return Response({"updated_orders": updated})

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
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return Response({"error": "Cart is empty"}, status=400)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                payment_status='pending',
                fulfillment_status='awaiting_shipment',
                total_price=0,
                shipping_address=request.data.get("shipping_address", ""),
                shipping_cost=request.data.get("shipping_cost", ""),
            )

            total = 0
            for item in cart.items.all():
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    gift_set=item.gift_set,
                    quantity=item.quantity,
                    message=item.message
                )

                if item.product:
                    item.product.stock -= item.quantity
                    item.product.save()
                    total += float(item.product.price) * item.quantity

                elif item.gift_set:
                    item.gift_set.stock -= item.quantity
                    item.gift_set.save()
                    total += float(item.gift_set.price) * item.quantity

                if item.charms.exists():
                    for cc in CartItemCharm.objects.filter(item=item):
                        OrderItemCharm.objects.create(order_item=order_item, charm=cc.charm)
                        total += float(cc.charm.price) * cc.quantity

                elif item.product is None and item.gift_set is None:
                    for cc in CartItemCharm.objects.filter(item=item):
                        OrderItemCharm.objects.create(order_item=order_item, charm=cc.charm)
                        total += float(cc.charm.price) * cc.quantity

                item.delete()

            order.total_price = total
            order.save()

            # Jadwalkan email & token setelah commit sukses
            transaction.on_commit(lambda: send_order_confirmation_email(order))
            transaction.on_commit(lambda: create_and_send_review_token(order))

        return Response({"order_id": order.id, "total_price": total})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def direct_checkout(request):
    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                payment_status='pending',
                fulfillment_status='awaiting_shipment',
                total_price=0,
                shipping_address=request.data.get("shipping_address", ""),
                shipping_cost=request.data.get("shipping_cost", "",),
            )

            quantity = int(request.data.get("quantity", 1))
            charms = request.data.get("charms", [])

            order_item = OrderItem.objects.create(
                order=order,
                product=None,
                gift_set=None,
                quantity=quantity,
                message=order_item.message
            )

            total = 0

            if "product" in request.data:
                product = get_object_or_404(Product, id=request.data["product"])
                order_item.product = product
                product.stock -= quantity
                product.save()
                total += float(product.price) * quantity

            elif "gift_set" in request.data:
                gift_set = get_object_or_404(GiftSetOrBundleMonthlySpecial, id=request.data["gift_set"])
                order_item.gift_set = gift_set
                gift_set.stock -= quantity
                gift_set.save()
                total += float(gift_set.price) * quantity

            if charms:
                charm_counts = Counter(charms)
                for charm_id, qty in charm_counts.items():
                    charm = get_object_or_404(Charm, id=charm_id)
                    for _ in range(qty):
                        OrderItemCharm.objects.create(order_item=order_item, charm=charm)
                    total += float(charm.price) * qty

            order_item.save()
            order.total_price = total
            order.save()

            transaction.on_commit(lambda: send_order_confirmation_email(order))
            transaction.on_commit(lambda: create_and_send_review_token(order))

        return Response({"order_id": order.id, "total_price": total})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def selective_checkout(request):
    cart_item_ids = request.data.get("cart_item_ids", [])
    if not cart_item_ids:
        return Response({"error": "Provide cart_item_ids"}, status=400)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                payment_status='pending',
                fulfillment_status='awaiting_shipment',
                total_price=0,
                shipping_address=request.data.get("shipping_address", ""),
                shipping_cost=request.data.get("shipping_cost", ""),
            )

            total = 0
            for cid in cart_item_ids:
                item = get_object_or_404(CartItem, id=cid, cart__user=request.user)

                oi = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    gift_set=item.gift_set,
                    quantity=item.quantity,
                    message=item.message
                )

                if item.product:
                    item.product.stock -= item.quantity
                    item.product.save()
                    total += float(item.product.price) * item.quantity

                elif item.gift_set:
                    item.gift_set.stock -= item.quantity
                    item.gift_set.save()
                    total += float(item.gift_set.price) * item.quantity

                # charms
                for cc in CartItemCharm.objects.filter(item=item):
                    OrderItemCharm.objects.create(order_item=oi, charm=cc.charm)
                    total += float(cc.charm.price) * cc.quantity

                item.delete()

            order.total_price = total
            order.save()
            transaction.on_commit(lambda: send_order_confirmation_email(order))
            transaction.on_commit(lambda: create_and_send_review_token(order))

        return Response({"order_id": order.id, "total_price": total})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    jet = JetService()
    data = request.data

    if not data:
        return Response({"error": "body is required"}, status=400)

    try:
        resp = jet.order(data=data)
        return Response(resp)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def cancel_order(request):
    jet = JetService()
    detail = request.data.get("detail")

    if not detail:
        return Response({"error": "detail is required"}, status=400)

    try:
        resp = jet.cancel_order(detail=detail)
        return Response(resp)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def check_tariff(request):
    jet = JetService()

    if not request.data:
        return Response({"error": "request body cannot be empty"}, status=400)

    try:
        resp = jet.tariff_check(data=request.data)
        return Response(resp)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def track_order(request):
    jet = JetService()
    awb = request.data.get("awb")

    if not awb:
        return Response({"error": "awb is required"}, status=400)

    try:
        resp = jet.track(awb=awb)
        return Response(resp)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def print_waybill(request):
    jet = JetService()
    billcode = request.data.get("billcode")

    if not billcode:
        return Response({"error": "billcode is required"}, status=400)

    try:
        resp = jet.print_waybill(billcode=billcode)
        return Response(resp)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

class JNTLocationListView(generics.ListAPIView):
    queryset = JNTLocation.objects.all()
    serializer_class = JNTLocationSerializer

class JNTOrderListCreateView(generics.ListCreateAPIView):
    queryset = JNTOrder.objects.all().order_by('-created_at')
    serializer_class = JNTOrderSerializer

# Retrieve, update, or delete a single order
class JNTOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = JNTOrder.objects.all()
    serializer_class = JNTOrderSerializer
    lookup_field = "orderid" 