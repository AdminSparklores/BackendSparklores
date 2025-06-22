from django.contrib import admin
from .models import Charm, DiscountedItem, GiftSetOrBundleMonthlySpecial, OrderItem, OrderItemCharm, Product, Order, Review, NewsletterSubscriber, Cart, CartItem, CartItemCharm, ProductImage, VideoContent, PageBanner, PhotoGallery, DiscountCampaign

@admin.register(Charm)
class CharmAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category',)
    search_fields = ['name']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'label', 'stock', 'details', 'rating', 'discount', 'charms', 'is_charm_spreadable')
    list_filter = ('category', 'label', 'charms', 'is_charm_spreadable')
    filter_horizontal = ('jewel_set_products',) 
    search_fields = ['name']
    inlines = [ProductImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'rating', 'uploaded_at')
    list_filter = ('rating',)

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_at')

class CartItemCharmInline(admin.TabularInline):
    model = CartItemCharm
    extra = 1
    autocomplete_fields = ['charm']

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    show_change_link = True
    autocomplete_fields = ['product', 'gift_set']
    readonly_fields = ['display_product_or_gift_set']
    fields = ['display_product_or_gift_set', 'product', 'gift_set', 'quantity']

    def display_product_or_gift_set(self, obj):
        if obj.product:
            return f"[Product] {obj.product.name}"
        elif obj.gift_set:
            return f"[GiftSet] {obj.gift_set.name}"
        return "-"
    display_product_or_gift_set.short_description = "Product / Gift Set"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_items', 'cart_owner')
    list_filter = ('created_at',)
    search_fields = ['user__email']
    inlines = [CartItemInline]

    def total_items(self, obj):
        return obj.items.count()
    total_items.short_description = "Jumlah Item"

    def cart_owner(self, obj):
        return obj.user.email
    cart_owner.short_description = "Pemilik Cart"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'display_product_or_gift_set', 'quantity')
    list_filter = ('product','gift_set')
    inlines = [CartItemCharmInline]
    autocomplete_fields = ['cart', 'product', 'gift_set']
    search_fields = ['cart__user__email', 'product__name', 'gift_set__name'] 

    def display_product_or_gift_set(self, obj):
        if obj.product:
            return f"[Product] {obj.product.name}"
        elif obj.gift_set:
            return f"[GiftSet] {obj.gift_set.name}"
        return "-"
    display_product_or_gift_set.short_description = "Produk / Gift Set"

@admin.register(CartItemCharm)
class CartItemCharmAdmin(admin.ModelAdmin):
    list_display = ('item', 'charm')
    list_filter = ('charm',)
    autocomplete_fields = ['item', 'charm']

@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
    search_fields = ['title']

@admin.register(PageBanner)
class PageBannerAdmin(admin.ModelAdmin):
    list_display = ('page', 'uploaded_at')
    search_fields = ['page']

@admin.register(PhotoGallery)
class PhotoGalleryAdmin(admin.ModelAdmin):
    list_display = ('alt_text','image', 'description', 'uploaded_at')
    search_fields = ['description']

class DiscountedItemInline(admin.TabularInline):
    model = DiscountedItem
    extra = 1

@admin.register(DiscountCampaign)
class DiscountCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'start_time', 'end_time')
    search_fields = ['name']
    inlines = [DiscountedItemInline]

@admin.register(DiscountedItem)
class DiscountedItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'campaign', 'discount_type', 'discount_value')
    list_filter = ('discount_type', 'campaign')
    search_fields = ['product__name']

@admin.register(GiftSetOrBundleMonthlySpecial)
class GiftSetOrBundleMonthlySpecialAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'price', 'created_at', 'is_monthly_special')
    list_filter = ('label',)
    search_fields = ('name',)
    filter_horizontal = ('products',)

class OrderItemCharmInline(admin.TabularInline):
    model = OrderItemCharm
    extra = 0

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'gift_set', 'quantity']
    show_change_link = True

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'payment_status', 'fulfillment_status', 'total_price', 'created_at')
    list_filter = ('payment_status', 'fulfillment_status', 'created_at')
    search_fields = ('user__email', 'id')
    inlines = [OrderItemInline]
    readonly_fields = ('total_price', 'created_at', 'updated_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'gift_set', 'quantity')
    inlines = [OrderItemCharmInline]
    search_fields = ('order__id', 'product__name')

@admin.register(OrderItemCharm)
class OrderItemCharmAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_item', 'charm')
    search_fields = ('order_item__order__id', 'charm__name')