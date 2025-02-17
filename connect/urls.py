from django.urls import path
from . import views

app_name = 'connect'

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('learninghub/', views.learninghub, name='learninghub'),
    
    # Authentication
    path('login/', views.custom_login, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Marketplace
    path('marketplace/', views.marketplacehome, name='marketplacehome'),
    path('product/<int:id>/', views.productdetails, name='productdetails'),
    path('product/add/', views.addproduct, name='addproduct'),
    path('product/edit/<int:id>/', views.editproduct, name='editproduct'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Dashboards
    path('dashboard/seller/', views.sellerdashboard, name='sellerdashboard'),
    path('dashboard/bodarider/', views.bodariderdashboard, name='bodariderdashboard'),
    path('dashboard/seller/edit/', views.editsellerprofile, name='editsellerprofile'),
    path('dashboard/buyer/', views.buyerdashboard, name='buyerdashboard'),
    path('dashboard/buyer/edit/', views.editbuyerprofile, name='editbuyerprofile'),
    path('dashboard/bodarider/edit/', views.editbodariderprofile, name='editbodariderprofile'),
    
    # M-Pesa Integration
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/stk-push/', views.initiate_stk_push, name='stk_push'),
    
    # Learning Hub
    path('courses/', views.coursecatalog, name='coursecatalog'),
    path('courses/<int:course_id>/', views.coursedetails, name='coursedetails'),

    # Community
    path('community/', views.communityhome, name='communityhome'),
    path('community/discussion/<int:discussion_id>/', views.discussiondetails, name='discussiondetails'),
    path('community/create/', views.creatediscussion, name='creatediscussion'),
    path('community/search/', views.searchresults, name='searchresults'),
    path('community/discussion/<int:discussion_id>/edit/', views.edit_discussion, name='edit_discussion'),
    path('community/discussion/<int:discussion_id>/delete/', views.delete_discussion, name='delete_discussion'),

    # Withdrawal
    path('withdraw-earnings/', views.withdraw_earnings, name='withdraw_earnings'),

    # Delivery
    path('order/<int:order_id>/update-delivery/', views.update_delivery_status, name='update_delivery_status'),
    path('order/<int:order_id>/confirm-delivery/', views.confirm_delivery, name='confirm_delivery'),

    # Cart
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Learning Hub
    path('learning-hub/add-article/', views.add_article, name='add_article'),
    path('learning-hub/add-course/', views.add_course, name='add_course'),

    # Admin Dashboard
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/users/', views.admin_user_list, name='user_list'),
    path('dashboard/admin/products/', views.admin_product_list, name='product_list'),
    path('dashboard/admin/orders/', views.admin_order_list, name='order_list'),
    path('dashboard/admin/earnings/', views.admin_earnings, name='earnings'),

    # Post
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),

    # Contact
    path('contact/leave-testimonial/', views.leave_testimonial, name='leave_testimonial'),

    # Payment
    path('payment/<int:order_id>/', views.payment, name='payment'),
     # Admin Dashboard - Remove decorators from here
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/users/', views.admin_user_list, name='user_list'),
    path('dashboard/admin/products/', views.admin_product_list, name='product_list'),
    path('dashboard/admin/orders/', views.admin_order_list, name='order_list'),

]
