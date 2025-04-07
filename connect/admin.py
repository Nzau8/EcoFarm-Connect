from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .models import (
    Category, Course, Lesson, Comment, Testimonial,
    User, Product, Order, DeliveryEarning, BodaRider,
    Seller, Buyer, Article, Discussion, Withdrawal,
    CourseEnrollment
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
    list_display = ('name', 'get_courses_count')
    search_fields = ('name',)

    def get_courses_count(self, obj):
        return obj.courses.count()
    get_courses_count.short_description = 'Number of Courses'

@admin.register(Course, site=custom_admin_site)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'instructor', 'level', 'duration', 'created_at']
    list_filter = ['category', 'level', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'instructor')

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

@admin.register(CourseEnrollment, site=custom_admin_site)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'completed', 'progress']
    list_filter = ['completed', 'enrolled_at']
    search_fields = ['user__username', 'course__title']
    readonly_fields = ['enrolled_at']
