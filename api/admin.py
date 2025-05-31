from django.contrib import admin
from .models import Charm, DiscountedItem, GiftSetOrBundleMonthlySpecial, Product, Order, Review, NewsletterSubscriber, Cart, CartItem, CartItemCharm, ProductImage, VideoContent, PageBanner, PhotoGallery, DiscountCampaign

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
    list_display = ('name', 'category', 'price', 'label', 'stock', 'details')
    list_filter = ('category', 'label')
    filter_horizontal = ('jewel_set_products',) 
    search_fields = ['name']
    inlines = [ProductImageInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'status')
    list_filter = ('status',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

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

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    show_change_link = True

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ['user__email']
    inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    list_filter = ('product',)
    inlines = [CartItemCharmInline]

@admin.register(CartItemCharm)
class CartItemCharmAdmin(admin.ModelAdmin):
    list_display = ('item', 'charm')
    list_filter = ('charm',)

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