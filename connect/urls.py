from django.urls import path
from . import views
from . import views_community  # Add import for community views
from django.conf import settings
from django.contrib.auth import views as auth_views  # Add this import

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
    path('product/add/', views.add_product, name='add_product'),  # Move this before product detail
    path('product/<int:id>/', views.productdetails, name='productdetails'),
    path('products/', views.product_list, name='productlist'),
    path('product/edit/<int:id>/', views.editproduct, name='editproduct'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/buyer/', views.buyerorders, name='buyerorders'),
    
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
    path('courses/', views.courses_list, name='courses'),
    path('courses/<int:course_id>/', views.coursedetails, name='coursedetails'),
    path('resources/', views.resources_list, name='resources'),
    path('progress/', views.learning_progress, name='progress'),

    # Community
    path('community/', views.community_home, name='community_home'),
    path('community/discussion/<int:discussion_id>/', views.discussiondetails, name='discussiondetails'),
    path('community/create/', views.creatediscussion, name='creatediscussion'),
    path('community/search/', views.searchresults, name='searchresults'),
    path('community/discussion/<int:discussion_id>/edit/', views.edit_discussion, name='edit_discussion'),
    path('community/discussion/<int:discussion_id>/delete/', views.delete_discussion, name='delete_discussion'),
    path('community/discussion/create/', views_community.create_discussion, name='create_discussion'),
    path('community/post/<int:post_id>/', views_community.post_detail, name='post_detail'),

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

    # Community URLs
    path('community/profile/edit/', views_community.edit_profile, name='edit_profile'),
    path('community/profile/update-picture/', views_community.update_profile_picture, name='update_profile_picture'),
    path('community/profile/<str:username>/', views_community.profile_view, name='profile'),

    # Post URLs
    path('community/post/create/', views_community.create_post, name='create_post'),
    path('community/post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('community/post/<int:post_id>/edit/', views_community.edit_post, name='edit_post'),
    path('community/post/<int:post_id>/delete/', views_community.delete_post, name='delete_post'),
    path('community/post/<int:post_id>/react/', views.toggle_reaction, name='toggle_reaction'),
    path('community/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),

    # Group URLs
    path('community/groups/', views_community.group_list, name='groups'),
    path('community/group/create/', views_community.create_group, name='create_group'),
    path('community/group/<int:group_id>/', views_community.group_detail, name='group_detail'),
    path('community/group/<int:group_id>/edit/', views_community.edit_group, name='edit_group'),
    path('community/group/<int:group_id>/join/', views.group_join_request, name='group_join_request'),
    path('community/group/<int:group_id>/leave/', views_community.leave_group, name='leave_group'),
    path('community/group/<int:group_id>/request-join/', views_community.request_join_group, name='request_join_group'),

    # Event URLs
    path('community/events/', views_community.event_list, name='events'),
    path('community/event/create/', views_community.create_event, name='create_event'),
    path('community/event/<int:event_id>/', views_community.event_detail, name='event_detail'),
    path('community/event/<int:event_id>/attend/', views_community.toggle_attendance, name='toggle_attendance'),

    # Live Stream URLs
    path('community/streams/', views_community.stream_list, name='live_streams'),
    path('community/stream/create/', views_community.create_live_stream, name='create_stream'),
    path('community/stream/<int:stream_id>/', views_community.stream_detail, name='stream_detail'),

    # Poll URLs
    path('community/polls/', views_community.poll_list, name='polls'),
    path('community/poll/create/', views_community.create_poll, name='create_poll'),
    path('community/poll/vote/', views_community.vote_poll, name='vote_poll'),

    # Hashtag URLs
    path('community/hashtag/<str:name>/', views_community.hashtag_view, name='hashtag'),
    path('community/category/<str:name>/', views_community.category_view, name='category'),

    # User Interaction URLs
    path('community/user/<int:user_id>/follow/', views_community.toggle_follow, name='toggle_follow'),
    path('community/user/<int:user_id>/block/', views_community.toggle_block_user, name='toggle_block'),
    path('community/chat/start/', views_community.start_chat, name='start_chat'),
    path('community/report/', views_community.report_content, name='report_content'),

    # Chat URLs
    path('community/chat/', views_community.chat_list, name='chat_list'),
    path('community/chat/<int:chat_id>/', views_community.chat_detail, name='chat_detail'),

    # New URLs
    path('community/comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),

    # Group Join Request URLs
    path('group/request/<int:request_id>/handle/', views.handle_join_request, name='handle_join_request'),

    # Review URLs
    path('product/<int:product_id>/review/', views.create_product_review, name='create_product_review'),
    path('seller/<int:seller_id>/review/', views.create_seller_review, name='create_seller_review'),
    path('product/<int:product_id>/reviews/', views.get_product_reviews, name='get_product_reviews'),
    path('seller/<int:seller_id>/reviews/', views.get_seller_reviews, name='get_seller_reviews'),

    # Community API endpoints
    path('api/posts/<int:post_id>/react/', views_community.toggle_reaction, name='react_to_post'),
    path('api/posts/<int:post_id>/comment/', views_community.add_comment, name='add_comment'),
]

# Add this only if DEBUG is True
if settings.DEBUG:
    urlpatterns += [
        path('debug/database/', views.debug_database, name='debug_database'),
    ]
