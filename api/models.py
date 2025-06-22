import os
from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class Charm(models.Model):
    CHARM_CATEGORY_CHOICES = [
        ('alphabet', 'Alphabet'),
        ('birthstone', 'Birthstone'),
        ('birthstone_mini', 'Birthstone Mini'),
        ('birth_flower', 'Birth Flower'),
        ('number', 'Number'),
        ('special', "Sparklore's Special"),
        ('zodiac', 'Zodiac'),
    ]

    LABEL_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('rose_gold', 'Rose Gold'),
        ('null', 'Null'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CHARM_CATEGORY_CHOICES)
    image = models.ImageField(upload_to='charms/')
    label = models.CharField(max_length=100, choices=LABEL_CHOICES, default='null')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    sold_stok = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.category})"
        
    def clean(self):
        if self.price is not None and self.price < 0:
            raise ValidationError("Harga charms tidak boleh negatif.")

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('necklace', 'Necklace'),
        ('bracelet', 'Bracelet'),
        ('earring', 'Earring'),
        ('ring', 'Ring'),
        ('anklet', 'Anklet'),
        ('jewel_set', 'Jewel Set'),
        ('charm', 'Charm'),
    ]

    LABEL_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('rose_gold', 'Rose Gold'),
        ('null', 'Null'),
    ]

    name = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    label = models.CharField(max_length=100, choices=LABEL_CHOICES)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    sold_stok = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    charms = models.BooleanField(default=False, help_text="Apakah produk ini memiliki charms?")
    is_charm_spreadable = models.BooleanField(default=False, help_text="Apakah produk ini charmsnya bisa disebarkan?")

    # Produk di dalam jewel set
    jewel_set_products = models.ManyToManyField('self', blank=True, symmetrical=False)

    def __str__(self):
        return f"{self.name} ({self.category})"
    
    def clean(self):
        if self.price < 0:
            raise ValidationError("Harga produk tidak boleh negatif.")
        if self.stock < 0:
            raise ValidationError("Stok tidak boleh negatif.")

def product_image_upload_path(instance, filename):
    return f"products/{instance.product.id}/{filename}"

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_upload_path)
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Gambar untuk {self.product.name}"

class GiftSetOrBundleMonthlySpecial(models.Model):
    LABEL_CHOICES = [
        ('forUs', 'For Us'),
        ('forHer', 'For Her'),
        ('forHim', 'For Him'),
        ('monthlySpecial', 'Monthly Special'),
        ('null', 'Null'),
    ]

    name = models.CharField(max_length=200)
    label = models.CharField(max_length=100, choices=LABEL_CHOICES, default='null')
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(Product, related_name='gift_sets')
    image = models.ImageField(upload_to='gift_sets/')
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.IntegerField(default=0)
    sold_stok = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_monthly_special = models.BooleanField(default=True, help_text="Apakah ini adalah produk spesial bulanan?")

    def __str__(self):
        return self.name
    
    def clean(self):
        if self.price < 0:
            raise ValidationError("Harga gift set tidak boleh negatif.")

class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    class FulfillmentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PACKING = 'packing', 'Packing'
        DELIVERY = 'delivery', 'Delivery'
        DONE = 'done', 'Done'
        NOT_ACCEPTED = 'not_accepted', 'Not Accepted'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    fulfillment_status = models.CharField(max_length=20, choices=FulfillmentStatus.choices, default=FulfillmentStatus.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.CharField(max_length=255)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} ({self.payment_status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    gift_set = models.ForeignKey(GiftSetOrBundleMonthlySpecial, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"OrderItem in Order #{self.order.id}"

class OrderItemCharm(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='charms')
    charm = models.ForeignKey(Charm, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.charm.name} in OrderItem #{self.order_item.id}"

class NewsletterSubscriber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

class Review(models.Model):
    user_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="review_images/", blank=True, null=True)
    products = models.ManyToManyField(Product)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user_name} - {self.rating}⭐"
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    gift_set = models.ForeignKey(GiftSetOrBundleMonthlySpecial, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    charms = models.ManyToManyField(Charm, blank=True, through='CartItemCharm')

    def __str__(self):
        product_name = self.product.name if self.product else (
            self.gift_set.name if self.gift_set else "No Product/Gift Set"
        )
        user_email = self.cart.user.email if self.cart and self.cart.user else "Unknown User"
        return f"{product_name} in {user_email}'s cart"
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Jumlah item harus lebih dari 0.")
        if self.product and self.product.stock < self.quantity:
            raise ValidationError("Stok tidak cukup untuk produk ini.")
        if self.product and self.gift_set:
            raise ValidationError("Hanya boleh memilih salah satu: product atau gift_set.")

class CartItemCharm(models.Model):
    item = models.ForeignKey(CartItem, on_delete=models.CASCADE)
    charm = models.ForeignKey(Charm, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        item = self.item
        product_name = item.product.name if item and item.product else (
            item.gift_set.name if item and item.gift_set else "Unknown Item"
        )
        user_email = item.cart.user.email if item and item.cart and item.cart.user else "Unknown User"
        return f"{self.charm.name}x{self.quantity} - {product_name} in {user_email}'s cart"

class VideoContent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class PageBanner(models.Model):
    PAGE_CHOICES = [
        ('homepage', 'Home Page'),
        ('new_arrival', 'New Arrival'),
        ('for_us', 'For Us'),
        ('for_him', 'For Him'),
        ('for_her', 'For Her'),
        ('jewel_set', 'Jewel Set'),
        ('charmbar', 'Charm Bar'),
        ('charms', 'Charms'),
        ('necklace', 'Necklace'),
        ('bracelet', 'Bracelet'),
        ('earrings', 'Earrings'),
        ('rings', 'Rings'),
        ('anklets', 'Anklets'),
        ('gift_sets', 'Gift Sets'),
        ('monthly_special', 'Monthly Special'),
    ]

    page = models.CharField(max_length=30, choices=PAGE_CHOICES, unique=True)
    image = models.ImageField(upload_to='banners/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_page_display()} Banner"
    
class PhotoGallery(models.Model):
    alt_text = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='photo_gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.alt_text
    
    def clean(self):
        if not self.image:
            raise ValidationError("Gambar harus diunggah untuk galeri foto.")
        if not self.alt_text:
            raise ValidationError("Judul/Alternative Text harus diisi untuk galeri foto.")

class DiscountCampaign(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.name

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class DiscountedItem(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage (%)'),
        ('amount', 'Fixed Amount (Rp)')
    ]

    campaign = models.ForeignKey(DiscountCampaign, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} in {self.campaign.name}"

    def clean(self):
        if self.discount_type == 'percent' and (self.discount_value < 0 or self.discount_value > 100):
            raise ValidationError("Diskon persentase harus antara 0-100%.")
        if self.discount_type == 'amount' and self.discount_value < 0:
            raise ValidationError("Diskon nominal tidak boleh negatif.")