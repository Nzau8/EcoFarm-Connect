from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .models import (
    Category, Course, Lesson, Comment, Testimonial,
    User, Product, Order, DeliveryEarning, BodaRider,
    Seller, Buyer, Article, Discussion, Withdrawal
)

class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        User = get_user_model()
        extra_context.update({
            'total_users': User.objects.count(),
            'total_products': Product.objects.count(),
            'total_orders': Order.objects.count(),
            'total_earnings': Order.objects.aggregate(total=Sum('delivery_fee'))['total'] or 0,
            'recent_orders': Order.objects.select_related('buyer').order_by('-created_at')[:10],
            'recent_users': User.objects.order_by('-date_joined')[:10]
        })
        return super().index(request, extra_context)

custom_admin_site = CustomAdminSite(name='custom_admin')

@admin.register(Category, site=custom_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Course, site=custom_admin_site)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'level', 'created_at_display')
    list_filter = ('category', 'level')
    search_fields = ('title', 'instructor__username')

    def created_at_display(self, obj):
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M')
        return "N/A"
    created_at_display.short_description = 'Created At'

@admin.register(Product, site=custom_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'stock', 'unit')
    list_filter = ('unit', 'delivery_available')
    search_fields = ('name', 'seller__company_name')

@admin.register(Order, site=custom_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_price', 'delivery_status', 'payment_status')
    list_filter = ('delivery_status', 'payment_status')
    search_fields = ('buyer__username', 'id')

@admin.register(User, site=custom_admin_site)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'date_joined')
    search_fields = ('username', 'email')

@admin.register(BodaRider, site=custom_admin_site)
class BodaRiderAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'status', 'get_rating')
    list_filter = ('status',)
    
    def get_rating(self, obj):
        return obj.get_rating()
    get_rating.short_description = 'Avg Rating'

@admin.register(Testimonial, site=custom_admin_site)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'truncated_content', 'user_type', 'rating', 'created_at')
    list_filter = ('user_type', 'rating')
    search_fields = ('name', 'content')
    
    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'

@admin.register(Seller, site=custom_admin_site)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'location', 'phone_number')
    search_fields = ('company_name', 'user__username')

@admin.register(Article, site=custom_admin_site)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'featured')
    list_filter = ('category', 'featured')
    search_fields = ('title', 'author__username')

@admin.register(Withdrawal, site=custom_admin_site)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('rider', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('rider__user__username', 'transaction_id')
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'some_field', 'another_field', 'created_at_display')

    def created_at_display(self, obj):
        return obj.created_at  # Ensure that Course actually has a created_at field.
    created_at_display.short_description = 'Created At'
