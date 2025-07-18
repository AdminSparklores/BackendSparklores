from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CharmViewSet, DiscountCampaignViewSet, GiftSetOrBundleMonthlySpecialViewSet, MidtransSnapTokenView, OrderViewSet, ProductViewSet, CartViewSet, ReviewViewSet, NewsletterSubscriberViewSet, VideoContentViewSet, PageBannerViewSet, PhotoGalleryViewSet, AdminOrderTableView, cancel_order, check_tariff, create_order, track_order, checkout, direct_checkout, selective_checkout

router = DefaultRouter()
router.register(r'charms', CharmViewSet, basename='charm')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'newsletters', NewsletterSubscriberViewSet, basename='newsletter')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'videos', VideoContentViewSet, basename='video')
router.register(r'page-banners', PageBannerViewSet, basename='pagebanner')
router.register(r'discount-campaigns', DiscountCampaignViewSet, basename='discountcampaign')
router.register(r'photo-gallery', PhotoGalleryViewSet, basename='photogallery')
router.register(r'gift-sets', GiftSetOrBundleMonthlySpecialViewSet, basename='giftsetorbundlemonthlyspecial')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/orders-table/', AdminOrderTableView.as_view(), name='admin-orders-table'),
    path('checkout/', checkout, name='checkout'),
    path('direct_checkout/', direct_checkout, name='direct_checkout'),
    path('selective_checkout/', selective_checkout, name='selective_checkout'),
    path('midtrans/token/', MidtransSnapTokenView.as_view(), name='midtrans_token'),
    path('jnt/order/', create_order, name='jnt_order'),
    path('jnt/cancel/', cancel_order, name='jnt_cancel'),
    path('jnt/track/', track_order, name='jnt_track'),
    path('jnt/tariff/', check_tariff, name='jnt_tariff'),
]
