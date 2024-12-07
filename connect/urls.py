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
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.orderconfirmation, name='orderconfirmation'),
    
    # Dashboards
    path('dashboard/seller/', views.sellerdashboard, name='sellerdashboard'),
    path('dashboard/bodarider/', views.bodariderdashboard, name='bodariderdashboard'),
    path('dashboard/seller/edit/', views.editsellerprofile, name='editsellerprofile'),
    path('dashboard/buyer/', views.buyerdashboard, name='buyerdashboard'),
    path('dashboard/buyer/edit/', views.editbuyerprofile, name='editbuyerprofile'),
    path('dashboard/bodarider/edit/', views.editbodariderprofile, name='editbodariderprofile'),
    
    # M-Pesa Integration
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    
    # Learning Hub
    path('courses/', views.coursecatalog, name='coursecatalog'),
    path('courses/<int:course_id>/', views.coursedetails, name='coursedetails'),

    # Community
    path('community/', views.communityhome, name='communityhome'),
    path('community/discussion/<int:discussion_id>/', views.discussiondetails, name='discussiondetails'),
    path('community/create/', views.creatediscussion, name='creatediscussion'),
    path('community/search/', views.searchresults, name='searchresults'),

    # Withdrawal
    path('withdraw-earnings/', views.withdraw_earnings, name='withdraw_earnings'),

    # Delivery
    path('order/<int:order_id>/update-delivery/', views.update_delivery_status, name='update_delivery_status'),
]
