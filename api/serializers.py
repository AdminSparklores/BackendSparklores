from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Charm, GiftSetOrBundleMonthlySpecial, JNTLocation, OrderItem, OrderItemCharm, Product, Order, Review, NewsletterSubscriber, CartItem, Cart, CartItemCharm, VideoContent, ProductImage, PageBanner, PhotoGallery, DiscountedItem, DiscountCampaign
from django.core.mail import send_mail
from django.conf import settings
import textwrap

User = get_user_model()

class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)  
    user_email = serializers.SerializerMethodField() 
    subscribed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'user_email', 'subscribed_at']

    def get_user_email(self, obj):
        return obj.user.email

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email not found. Please login first")

        if NewsletterSubscriber.objects.filter(user=user).exists():
            raise serializers.ValidationError("Email has been registered.")
        
        self.user = user
        return value

    def create(self, validated_data):
        user = self.user  

        subscriber = NewsletterSubscriber.objects.create(user=user)

        message = textwrap.dedent(f"""\
            Hi {user.first_name or user.email},

            Thank you for subscribing to the Sparklore newsletter!

            We’re excited to share updates, offers, and more with you.

            - Sparklore Team
        """)

        send_mail(
            subject="Welcome to the Sparklore Newsletter",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return subscriber

class CharmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charm
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

class ProductSerializer(serializers.ModelSerializer):
    jewel_set_products = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all(), required=False)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def validate(self, data):
        category = data.get('category', None)
        charms = data.get('charms', [])
        jewel_set_products = data.get('jewel_set_products', [])

        if category == 'gift_set':
            if not jewel_set_products:
                raise serializers.ValidationError("Gift set harus berisi minimal satu produk.")
            for p in jewel_set_products:
                if p.category not in ['necklace', 'bracelet', 'earring', 'ring', 'anklet']:
                    raise serializers.ValidationError(f"Produk gift set hanya boleh berisi kategori: necklace, bracelet, earring, ring, anklet.")
        else:
            if jewel_set_products:
                raise serializers.ValidationError("Field gift_set_products hanya boleh diisi untuk kategori 'gift_set'.")
            
        return data

class ReviewSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all(), required=False)
    charms = serializers.PrimaryKeyRelatedField(many=True, queryset=Charm.objects.all(), required=False)
    gift_sets = serializers.PrimaryKeyRelatedField(many=True, queryset=GiftSetOrBundleMonthlySpecial.objects.all(), required=False)
    image = serializers.ImageField(required=False)

    class Meta:
        model = Review
        fields = '__all__'

    def create(self, validated_data):
        products = validated_data.pop('products', [])
        charms = validated_data.pop('charms', [])
        gift_sets = validated_data.pop('gift_sets', [])
        user = self.context['request'].user

        review = Review.objects.create(
            user_name=user.email or user.username,
            user_email=user.email,
            **validated_data
        )
        
        if products:
            review.products.set(products)
        if charms:
            review.charms.set(charms)
        if gift_sets:
            review.gift_sets.set(gift_sets)

        return review

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating harus antara 1 dan 5.")
        return value

class ProductInGiftSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'price', 'label']

class GiftSetOrBundleMonthlySpecialProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    products = ProductInGiftSetSerializer(many=True, read_only=True)

    class Meta:
        model = GiftSetOrBundleMonthlySpecial
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

class VideoContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = '__all__'

class PageBannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PageBanner
        fields = ['page', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class PhotoGalerySerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoGallery
        fields = ['id', 'image', 'alt_text']

class DiscountedItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = DiscountedItem
        fields = ['product', 'discount_type', 'discount_value']

class DiscountCampaignSerializer(serializers.ModelSerializer):
    items = DiscountedItemSerializer(many=True, read_only=True)

    class Meta:
        model = DiscountCampaign
        fields = ['id', 'name', 'description', 'start_time', 'end_time', 'items']

class OrderItemCharmSerializer(serializers.ModelSerializer):
    charm_name = serializers.CharField(source='charm.name', read_only=True)

    class Meta:
        model = OrderItemCharm
        fields = ['id', 'charm', 'charm_name']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    gift_set_name = serializers.CharField(source='gift_set.name', read_only=True)
    charms = OrderItemCharmSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'gift_set', 'gift_set_name', 'quantity', 'charms', 'message']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email',
            'payment_status', 'fulfillment_status',
            'total_price', 'shipping_address', 'shipping_cost', 'rejection_reason',
            'items', 'created_at', 'updated_at', 'weight',
        ]
        read_only_fields = ['created_at', 'updated_at']

def humanize_timesince(dt):
        now = timezone.now()
        delta = now - dt

        seconds = int(delta.total_seconds())
        periods = [
            ('year', 60 * 60 * 24 * 365),
            ('month', 60 * 60 * 24 * 30),
            ('week', 60 * 60 * 24 * 7),
            ('day', 60 * 60 * 24),
            ('hour', 60 * 60),
            ('minute', 60),
            ('second', 1)
        ]

        strings = []

        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value > 0:
                    strings.append(f"{period_value} {period_name}{'s' if period_value !=1 else ''}")
            if len(strings) >= 3:
                break

        if not strings:
            return "just now"

        return ' '.join(strings) + " ago"

class OrderTableSerializer(serializers.ModelSerializer):
    time_elapsed = serializers.SerializerMethodField()
    product_summary = OrderItemSerializer(many=True, read_only=True, source='items')
    message = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_email', 'time_elapsed', 'created_at', 'product_summary',
            'message', 'total_price', 'fulfillment_status'
        ]

    def get_time_elapsed(self, obj):
        return humanize_timesince(obj.created_at)

    def get_message(self, obj):
        return obj.rejection_reason or "No message"

class CartItemCharmSerializer(serializers.ModelSerializer):
    class Meta: model = CartItemCharm; fields = ['charm_id']

class CartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(required=False, default=1)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)
    gift_set = serializers.PrimaryKeyRelatedField(queryset=GiftSetOrBundleMonthlySpecial.objects.all(), required=False)

    charms_input = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    charms = serializers.SerializerMethodField(read_only=True)
    source_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'gift_set', 'quantity', 'charms_input', 'charms', 'source_type', 'message']

    def get_source_type(self, obj):
        if obj.product:
            return 'product'
        elif obj.gift_set:
            return 'gift_set'
        return 'charms_only'

    def get_charms(self, obj):
        charm_items = CartItemCharm.objects.filter(item=obj)
        result = []
        for charm_item in charm_items:
            result.extend([charm_item.charm.id] * charm_item.quantity)
        return result

    def validate(self, data):
        product = data.get('product') if 'product' in data else getattr(self.instance, 'product', None)
        gift_set = data.get('gift_set') if 'gift_set' in data else getattr(self.instance, 'gift_set', None)
        charms = data.get('charms', [])

        if gift_set and (product or charms):
            raise serializers.ValidationError('Gift set tidak boleh dikombinasikan dengan produk atau charms.')
        if len(charms) > 5:
            raise serializers.ValidationError('Max 5 charms per item.')
        if product and charms:
            if product.category not in ['necklace', 'bracelet']:
                raise serializers.ValidationError('Charms hanya bisa ditambahkan ke produk kategori necklace atau bracelet.')
        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    class Meta: model = Cart; fields = ['id','items']

class JNTLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JNTLocation
        fields = '__all__'