from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch, Count
from django.db import models, connection
from .forms import ProductForm
from .models import (
    Product, Order, Seller, BodaRider, Buyer,
    DeliveryEarning, OrderItem, Cart, Testimonial,
    Discussion, Post, Tag, Category, Course, Comment,
    User, CourseEnrollment, Article, Wishlist, Withdrawal,
    DeliveryAddress, Notification, Negotiation, Chat, Message,
    ContactMessage, GroupJoinRequest, Group, Resource, UserProgress
)
from .forms import (
    CustomUserCreationForm, DiscussionForm, PostForm,
    SellerProfileForm, BuyerProfileForm, BodaRiderProfileForm,ContactForm
)
from .mpesa import initiate_stk_push as process_mpesa_payment
from .services import DeliveryAllocationService, ReviewService
import json
from django.contrib.admin.views.decorators import staff_member_required
import logging
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.humanize.templatetags.humanize import naturaltime
from .signals import user_joined_group, user_left_group
from django.core.cache import cache
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import cache_page

# Initialize logger
logger = logging.getLogger(__name__)

def home(request):
    # Get active testimonials without relying on is_active
    testimonials = Testimonial.objects.all()  # Updated to remove is_active filter
    
    context = {
        'testimonials': testimonials,
    }
    return render(request, 'connect/home.html', context)

def about(request):
    context = {
        'stats': {
            'farmers': '1000+',
            'customers': '5000+',
            'riders': '200+'
        }
    }
    return render(request, 'connect/about.html', context)

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
import logging
from .forms import ContactForm
from .models import ContactMessage  # Adjust the import based on your models location

logger = logging.getLogger(__name__)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save to database
                ContactMessage.objects.create(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    subject=form.cleaned_data['subject'],
                    message=form.cleaned_data['message']
                )

                # Send email notification directly to you
                email_subject = f'New Contact Form Submission: {form.cleaned_data["subject"]}'
                email_message = f"""
                You have received a new message from the contact form:
                
                Name: {form.cleaned_data['name']}
                Email: {form.cleaned_data['email']}
                Subject: {form.cleaned_data['subject']}
                Message:
                {form.cleaned_data['message']}
                """

                send_mail(
                    email_subject,
                    email_message,
                    settings.EMAIL_HOST_USER,  # The email sender
                    ['nzau878@gmail.com'],  # email to receive the message directly
                    fail_silently=False,
                )

                messages.success(request, 'Thank you for your message! We will get back to you soon.')
                return redirect('connect:contact')

            except Exception as e:
                logger.error(f"Contact form error: {str(e)}")
                messages.error(request, 'Sorry, there was an error processing your message. Please try again later.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ContactForm()

    return render(request, 'connect/contact.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            
            if role == 'seller':
                Seller.objects.create(
                    user=user, 
                    company_name=form.cleaned_data['company_name'],
                    location=form.cleaned_data['location'],
                    phone_number=form.cleaned_data['phone_number'],
                    email=form.cleaned_data['email']
                )
            elif role == 'bodarider':
                BodaRider.objects.create(
                    user=user,
                    bike_model=form.cleaned_data['bike_model'],
                    license_number=form.cleaned_data['license_number'],
                    location=form.cleaned_data['location'],
                    phone_number=form.cleaned_data['phone_number']
                )
            elif role == 'buyer':
                Buyer.objects.create(
                    user=user,
                    phone_number=form.cleaned_data['phone_number'],
                    email=form.cleaned_data['email'],
                    address=form.cleaned_data['address']
                )
            
            # Log the user in
            user = authenticate(username=form.cleaned_data['username'], 
                              password=form.cleaned_data['password1'])
            if user:
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('connect:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'connect/signup.html', {'form': form})

def about(request):
    # Get counts
    sellers_count = Seller.objects.count()
    buyers_count = Buyer.objects.count()
    riders_count = BodaRider.objects.count()

    # Format numbers (add + only if there are entries)
    def format_count(count):
        if count > 0:
            return f"{count}+"
        return "0"

    context = {
        'team_members': [
            {
                'name': 'John Doe',
                'role': 'Founder & CEO',
                'image': 'team/team1.jpg'
            },
            # Add more team members as needed
        ],
        'stats': {
            'farmers': format_count(sellers_count),
            'customers': format_count(buyers_count),
            'riders': format_count(riders_count)
        }
    }
    return render(request, 'connect/about.html', context)
def contact(request):
    return render(request, 'connect/contact.html')
def learninghub(request):
    categories = Category.objects.all()
    featured_courses = Course.objects.all()[:3]
    
    # Get total unique learners (users enrolled in at least one course)
    total_learners = User.objects.filter(enrollments__isnull=False).distinct().count()
    
    # Get featured articles
    featured_articles = Article.objects.filter(featured=True).order_by('-created_at')[:3]
    
    # Get latest articles
    latest_articles = Article.objects.order_by('-created_at')[:5]
    
    context = {
        'categories': categories,
        'featured_courses': featured_courses,
        'total_courses': Course.objects.count(),
        'total_learners': total_learners,
        'featured_articles': featured_articles,
        'latest_articles': latest_articles,
        'is_admin': request.user.is_staff
    }
    return render(request, 'connect/learninghub.html', context)

def coursecatalog(request):
    courses = Course.objects.all()
    categories = Category.objects.all()
    selected_category = request.GET.get('category')
    if selected_category:
        courses = courses.filter(category__id=selected_category)
    return render(request, 'connect/coursecatalog.html', {
        'courses': courses, 
        'categories': categories,
        'selected_category': selected_category
    })

@login_required
def coursedetails(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    comments = course.comments.all().order_by('-created_at')
    is_enrolled = False
    
    if request.user.is_authenticated:
        is_enrolled = CourseEnrollment.objects.filter(
            user=request.user, 
            course=course
        ).exists()
    
    if request.method == "POST":
        if 'enroll' in request.POST:
            # Handle enrollment
            if not is_enrolled:
                CourseEnrollment.objects.create(
                    user=request.user,
                    course=course
                )
                messages.success(request, "Successfully enrolled in the course!")
                return redirect('connect:coursedetails', course_id=course_id)
        
        elif request.POST.get('comment'):
            # Handle comment
            comment_text = request.POST.get('comment')
            if comment_text:
                Comment.objects.create(
                    user=request.user,
                    course=course,
                    text=comment_text
                )
                messages.success(request, "Comment posted successfully!")
                return redirect('connect:coursedetails', course_id=course_id)
    
    return render(request, 'connect/coursedetails.html', {
        'course': course,
        'lessons': lessons,
        'comments': comments,
        'is_enrolled': is_enrolled
    })


# View for the community home page
def community_home(request):
    tag_filter = request.GET.get('tag')
    search_query = request.GET.get('query')

    discussions = Discussion.objects.all().order_by('-created_at')
    tags = Tag.objects.all()

    if search_query:
        # Split search query into keywords
        keywords = search_query.split()
        query = Q()
        
        # Search in titles
        for keyword in keywords:
            query |= Q(title__icontains=keyword)
            # Search in tags
            query |= Q(tags__name__icontains=keyword)
        
        discussions = discussions.filter(query).distinct()
    
    if tag_filter:
        discussions = discussions.filter(tags__name=tag_filter)
    
    return render(request, 'connect/community/home.html', {
        'discussions': discussions,
        'tags': tags,
        'tag_filter': tag_filter,
        'search_query': search_query
    })

# View for discussion details and posts
def discussiondetails(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    posts = discussion.posts.all().order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        content = request.POST.get('content')
        
        if content:
            Post.objects.create(
                user=request.user,
                discussion=discussion,
                content=content
            )
            return redirect('connect:discussiondetails', discussion_id=discussion.id)
    
    return render(request, 'connect/discussiondetails.html', {
        'discussion': discussion,
        'posts': posts,
    })

# View for creating a new discussion
@login_required
def creatediscussion(request):
    if request.method == 'POST':
        print("POST data:", request.POST)  # Keep this debug line
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.user = request.user
            discussion.save()

            # Handle tags - get from hidden input
            tags_input = request.POST.get('tagsList', '')  # Changed from 'tags' to 'tagsList'
            if tags_input:
                tag_names = tags_input.split(',')
                for tag_name in tag_names:
                    if tag_name.strip():  # Only process non-empty tags
                        tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                        discussion.tags.add(tag)

            messages.success(request, "Discussion created successfully!")
            return redirect('connect:community_home')
        else:
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DiscussionForm()

    return render(request, 'connect/creatediscussion.html', {'form': form})

# searching discussions
def searchresults(request):
    query = request.GET.get('query')
    discussions = Discussion.objects.filter(title__icontains=query)

    return render(request, 'searchresults.html', {
        'discussions': discussions,
        'query': query,
    })

# 1. Marketplace Home
@cache_page(60 * 5)
def marketplacehome(request):
    # Get filter parameters
    filters = {
        'category': request.GET.get('category'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'location': request.GET.get('location'),
        'availability': request.GET.get('availability'),
        'search': request.GET.get('search', ''),
    }
    
    # Build query
    products = Product.objects.select_related(
        'seller', 'category'
    ).prefetch_related(
        'orderitem_set'
    ).order_by('-created_at')
    
    # Apply filters
    if filters['search']:
        products = products.filter(
            Q(name__icontains=filters['search']) |
            Q(description__icontains=filters['search'])
        )
    
    if filters['category']:
        products = products.filter(category_id=filters['category'])
    
    if filters['min_price']:
        products = products.filter(price__gte=filters['min_price'])
    
    if filters['max_price']:
        products = products.filter(price__lte=filters['max_price'])
    
    if filters['location']:
        products = products.filter(location__icontains=filters['location'])
    
    if filters['availability'] == 'in_stock':
        products = products.filter(stock__gt=0)
    elif filters['availability'] == 'out_of_stock':
        products = products.filter(stock=0)
    
    # Cache categories and locations
    categories = cache.get('product_categories')
    if not categories:
        categories = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)
        cache.set('product_categories', categories, 60 * 60)  # Cache for 1 hour
    
    locations = cache.get('product_locations')
    if not locations:
        locations = Product.objects.values_list(
            'location', flat=True
        ).distinct()
        cache.set('product_locations', locations, 60 * 60)
    
    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)
    
    context = {
        'products': products,
        'categories': categories,
        'locations': locations,
        'filters': filters,
    }
    
    return render(request, 'connect/marketplacehome.html', context)

# 2. Product Details
@require_http_methods(["GET"])
def productdetails(request, id):
    # Get product with related data
    product = get_object_or_404(
        Product.objects.select_related(
            'seller', 'category'
        ).prefetch_related(
            'orderitem_set'
        ),
        id=id
    )
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    ).select_related(
        'seller'
    )[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
        'delivery_options': product.get_delivery_options(),
    }
    
    return render(request, 'connect/productdetails.html', context)

def cart(request):
    user = request.user

    if user.is_authenticated:
        # Logged-in users: Fetch cart from the database
        cart_items = Cart.objects.filter(user=user)
    else:
        # Guest users: Fetch cart from session
        cart_items = []
        session_cart = request.session.get('cart', {})

        for product_id, item in session_cart.items():
            product = Product.objects.get(id=int(product_id))
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'subtotal': product.price * item['quantity']
            })

    # Calculate total price
    total_price = sum(item['subtotal'] for item in cart_items) if not user.is_authenticated else sum(item.product.price * item.quantity for item in cart_items)

    return render(request, 'connect/cart.html', {'cart_items': cart_items, 'total_price': total_price})
# 4. Checkout
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('connect:cart')

    # Group cart items by seller
    sellers_items = {}
    for item in cart_items:
        if item.product.seller not in sellers_items:
            sellers_items[item.product.seller] = []
        sellers_items[item.product.seller].append(item)

    if request.method == 'POST':
        delivery_addresses = DeliveryAddress.objects.filter(user=request.user)
        selected_address = request.POST.get('delivery_address')
        delivery_instructions = request.POST.get('delivery_instructions', '')
        contact_number = request.POST.get('contact_number', '')

        # Process each seller's items as a separate order
        for seller, items in sellers_items.items():
            subtotal = sum(item.product.price * item.quantity for item in items)
            delivery_method = request.POST.get(f'delivery_method_{seller.id}')
            delivery_fee = 0

            # Calculate delivery fee based on method
            if delivery_method == 'BODA':
                delivery_fee = 200  # Base fee for boda delivery
            elif delivery_method == 'SELLER':
                delivery_fee = seller.delivery_fee if hasattr(seller, 'delivery_fee') else 150

            total_price = subtotal + delivery_fee

            # Create the order
            order = Order.objects.create(
                buyer=request.user,
                seller=seller,
                total_price=total_price,
                delivery_method=delivery_method,
                delivery_fee=delivery_fee,
                delivery_address=selected_address,
                delivery_instructions=delivery_instructions,
                contact_number=contact_number
            )

            # Create order items
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity
                )

            # If boda delivery is selected, assign the chosen rider
            if delivery_method == 'BODA':
                rider_id = request.POST.get(f'rider_{seller.id}')
                if rider_id:
                    rider = BodaRider.objects.get(id=rider_id)
                    order.assigned_rider = rider
                    order.delivery_status = 'ASSIGNED'
                    order.save()
                    
                    # Update rider status
                    rider.status = 'On Delivery'
                    rider.save()
                    
                    # Create notification for the rider
                    Notification.objects.create(
                        user=rider.user,
                        message=f'New delivery assignment for Order #{order.id}'
                    )

            # Create notifications
            Notification.objects.create(
                user=seller.user,
                message=f'New order received! Order #{order.id}'
            )
            
            Notification.objects.create(
                user=request.user,
                message=f'Order #{order.id} has been placed successfully'
            )

            # Clear cart items for this seller
            Cart.objects.filter(user=request.user, product__seller=seller).delete()

        return redirect('connect:order_confirmation', order_id=order.id)

    # Get all delivery addresses for the user
    delivery_addresses = DeliveryAddress.objects.filter(user=request.user)
    
    # Get available riders
    available_riders = BodaRider.objects.filter(status='Available')
    
    context = {
        'cart_items': cart_items,
        'sellers_items': sellers_items,
        'delivery_addresses': delivery_addresses,
        'available_riders': available_riders,
        'total': sum(item.product.price * item.quantity for item in cart_items),
    }
    return render(request, 'connect/checkout.html', context)

# 5. Order Confirmation
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'connect/order_confirmation.html', {
        'order': order,
    })

# 6. Buyer Orders
@login_required
def buyerorders(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, 'connect/buyerorders.html', {'orders': orders})

# 7. Order History
def orderhistory(request):
    orders = Order.objects.filter(user=request.user).order_by('-date_placed')
    return render(request, 'orderhistory.html', {'orders': orders})

# 8. Seller Dashboard
@login_required
def sellerdashboard(request):
    try:
        seller = get_object_or_404(Seller, user=request.user)
        products = Product.objects.filter(seller=seller)
        orders = Order.objects.filter(products__seller=seller).distinct()
        
        # Calculate analytics
        total_sales = sum(order.total_price for order in orders)
        total_products = products.count()
        pending_orders = orders.filter(status='Pending').count()
        
        context = {
            'seller': seller,
            'products': products,
            'orders': orders,
            'total_sales': total_sales,
            'total_products': total_products,
            'pending_orders': pending_orders,
        }
        return render(request, 'connect/sellerdashboard.html', context)
    except Seller.DoesNotExist:
        messages.error(request, "Seller profile not found. Please contact support.")
        return redirect('connect:home')

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user.seller
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('connect:sellerdashboard')  # Redirect to seller dashboard
    else:
        form = ProductForm()
    
    return render(request, 'connect/addproduct.html', {'form': form})

# 10. Edit Product (Seller)
def editproduct(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.save()
        return redirect('product_details', id=product.id)
    return render(request, 'editproduct.html', {'product': product})

# 11. Seller Orders
def sellerorders(request):
    seller = get_object_or_404(Seller, user=request.user)
    orders = Order.objects.filter(product__seller=seller)
    return render(request, 'sellerorders.html', {'orders': orders})

# 12. Negotiation Chats
@login_required
def negotiationchats(request):
    # Update to filter by buyer or seller
    negotiations = Negotiation.objects.filter(
        Q(buyer=request.user) | Q(seller__user=request.user)
    )
    return render(request, 'connect/negotiationchats.html', {'negotiations': negotiations})

# 13. Wishlist
@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'connect/wishlist.html', {'wishlist_items': wishlist_items})

# 14. Delivery Tracking
@login_required
def deliverytracking(request, order_id):
    # Check if user is buyer or seller of the order
    order = get_object_or_404(
        Order, 
        Q(buyer=request.user) | Q(products__seller__user=request.user),
        id=order_id
    )
    return render(request, 'connect/deliverytracking.html', {'order': order})

# 15. Chatbox (All Chats)
@login_required
def chatbox(request):
    # Get all chats where user is a participant
    chats = Chat.objects.filter(participants=request.user)
    return render(request, 'connect/chatbox.html', {'chats': chats})

# 16. Chatbox Frame (Specific Chat)
@login_required
def chatboxframe(request, chat_id):
    # Ensure user is a participant in the chat
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    messages = chat.messages.all().order_by('timestamp')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                content=message_content
            )
            # Optionally create a notification for other participants
            for participant in chat.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    user=participant,
                    message=f"New message from {request.user.username}"
                )
    
    return render(request, 'connect/chatboxframe.html', {
        'chat': chat, 
        'messages': messages
    })

# 17. Notifications
def notifications(request):
    notifications = request.user.notifications.all()
    return render(request, 'notification.html', {'notifications': notifications})


from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import login, authenticate

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            
            # Depending on the role, create the corresponding profile
            if role == 'seller':
                Seller.objects.create(user=user, company_name=form.cleaned_data['company_name'], 
                                    location=form.cleaned_data['location'], phone_number=form.cleaned_data['phone_number'])
            elif role == 'bodarider':
                BodaRider.objects.create(user=user, bike_model=form.cleaned_data['bike_model'], 
                                       license_number=form.cleaned_data['license_number'], phone_number=form.cleaned_data['phone_number'])
            elif role == 'buyer':
                Buyer.objects.create(user=user, phone_number=form.cleaned_data['phone_number'])
            
            # Log the user in
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            return redirect('connect:home')  # Redirect to home or dashboard after successful signup
    else:
        form = CustomUserCreationForm()

    return render(request, 'connect/signup.html', {'form': form})

from django.shortcuts import redirect
from django.contrib.auth import login

def custom_login(request):
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Check if there's a next URL parameter
            if next_url:
                return redirect(next_url)
            
            # Redirect based on user type
            if hasattr(user, 'seller'):
                return redirect('connect:sellerdashboard')
            elif hasattr(user, 'buyer'):
                return redirect('connect:buyerdashboard')
            elif hasattr(user, 'bodarider'):
                return redirect('connect:bodariderdashboard')
            return redirect('connect:home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'connect/login.html', {
        'form': form,
        'next': next_url
    })


# Unified Profile View
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    user = request.user

    # Redirect to the respective dashboard based on user type
    if hasattr(user, 'seller'):
        return redirect('connect:sellerdashboard')
    elif hasattr(user, 'buyer'):
        return redirect('connect:buyerdashboard')
    elif hasattr(user, 'bodarider'):
        return redirect('connect:bodariderdashboard')
    else:
        return redirect('connect:login')

@login_required
def buyerdashboard(request):
    try:
        buyer = request.user.buyer
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
        pending_confirmations = orders.filter(
            delivery_status='DELIVERED',
            delivery_confirmed_at__isnull=True
        )
        
        context = {
            'buyer': buyer,
            'orders': orders,
            'pending_confirmations': pending_confirmations,
            # ... other context data ...
        }
        return render(request, 'connect/buyerdashboard.html', context)
    except Buyer.DoesNotExist:
        messages.error(request, "Buyer profile not found.")
        return redirect('connect:home')

@login_required
def bodariderdashboard(request):
    try:
        bodarider = request.user.bodarider
        # Get all orders assigned to this boda rider
        deliveries = Order.objects.filter(assigned_rider=bodarider)
        
        # Calculate earnings
        earnings = DeliveryEarning.objects.filter(rider=bodarider)
        total_earnings = sum(earning.amount for earning in earnings)
        pending_earnings = sum(earning.amount for earning in earnings.filter(paid=False))
        paid_earnings = sum(earning.amount for earning in earnings.filter(paid=True))
        
        # Get recent earnings
        recent_earnings = earnings.order_by('-created_at')[:10]
        
        context = {
            'bodarider': bodarider,
            'deliveries': deliveries,
            'total_deliveries': deliveries.count(),
            'pending_deliveries': deliveries.filter(status='Pending').count(),
            'completed_deliveries': deliveries.filter(status='Delivered').count(),
            'total_earnings': total_earnings,
            'pending_earnings': pending_earnings,
            'paid_earnings': paid_earnings,
            'recent_earnings': recent_earnings,
        }
        return render(request, 'connect/bodariderdashboard.html', context)
    except BodaRider.DoesNotExist:
        messages.error(request, "Boda Rider profile not found.")
        return redirect('connect:home')


# Edit Profile for Seller
@login_required
def editsellerprofile(request):
    user = request.user
    seller = get_object_or_404(Seller, user=user)
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('connect:sellerdashboard')
    else:
        form = SellerProfileForm(instance=seller)
    
    return render(request, 'connect/editprofile.html', {
        'form': form,
        'profile_type': 'Seller'
    })

# Edit Profile for Buyer
@login_required
def editbuyerprofile(request):
    user = request.user
    buyer = get_object_or_404(Buyer, user=user)
    
    if request.method == 'POST':
        form = BuyerProfileForm(request.POST, instance=buyer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('connect:buyerdashboard')
    else:
        form = BuyerProfileForm(instance=buyer)
    
    return render(request, 'connect/editprofile.html', {
        'form': form,
        'profile_type': 'Buyer'
    })

# Edit Profile for Boda Rider
@login_required
def editbodariderprofile(request):
    user = request.user
    boda_rider = get_object_or_404(BodaRider, user=user)
    
    if request.method == 'POST':
        form = BodaRiderProfileForm(request.POST, instance=boda_rider)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('connect:bodariderdashboard')
    else:
        form = BodaRiderProfileForm(instance=boda_rider)
    
    return render(request, 'connect/editprofile.html', {
        'form': form,
        'profile_type': 'Boda Rider'
    })

class CustomLogoutView(LoginRequiredMixin, TemplateView):
    template_name = 'connect/logout.html'
    
    def get(self, request, *args, **kwargs):
        return self.render_to_response({})
    
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('connect:home')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Compose email message
        email_subject = f'New Contact Form Submission: {subject}'
        email_message = f"""
        You have received a new message from the contact form:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        try:
            # Send email
            send_mail(
                email_subject,
                email_message,
                settings.EMAIL_HOST_USER,  # From email
                ['myemail.email@gmail.com'],  
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            
        return redirect('connect:contact')
    
    return render(request, 'connect/contact.html')

@login_required
def initiate_payment(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        order_id = request.POST.get('order_id')
        
        try:
            response = process_mpesa_payment(
                phone_number=phone_number,
                amount=float(amount),
                account_reference=f"ORDER-{order_id}"
            )
            
            if response.get('ResponseCode') == '0':
                messages.success(request, "Payment initiated. Please check your phone.")
                request.session['checkout_request_id'] = response.get('CheckoutRequestID')
                return JsonResponse({'status': 'success', 'message': 'Check your phone to complete payment'})
            else:
                return JsonResponse({
                    'status': 'error', 
                    'message': response.get('ResponseDescription', 'Failed to initiate payment')
                })
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def mpesa_callback(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            logger.info(f"M-Pesa Callback Data: {data}")
            
            # Extract payment details
            result_code = data.get('ResultCode')
            transaction_id = data.get('MpesaReceiptNumber')
            amount = data.get('Amount')
            
            if result_code == 0:  # Payment successful
                # Update order status
                order = Order.objects.get(id=data.get('BillRefNumber').split('-')[1])
                order.payment_status = 'COMPLETED'
                order.mpesa_transaction_id = transaction_id
                order.save()
                
                # Create delivery earnings if rider assigned
                if order.assigned_rider:
                    DeliveryEarning.objects.create(
                        rider=order.assigned_rider,
                        order=order,
                        amount=order.delivery_fee,
                        paid=False
                    )
                
                # Send success notification
                messages.success(request, "Payment completed successfully!")
                return JsonResponse({'status': 'success'})
            else:
                messages.error(request, "Payment failed. Please try again.")
                return JsonResponse({'status': 'failed'})
                
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        
    except Exception as e:
        logger.error(f"M-Pesa Callback Error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def withdraw_earnings(request):
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            phone_number = request.POST.get('phone_number')
            rider = request.user.bodarider
            
            # Check if rider has sufficient balance
            pending_earnings = DeliveryEarning.objects.filter(
                rider=rider, 
                paid=False
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            if amount > pending_earnings:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Insufficient balance'
                })
            
            # Create withdrawal record
            withdrawal = Withdrawal.objects.create(
                rider=rider,
                amount=amount,
                phone_number=phone_number
            )
            
            # Initiate M-Pesa payment
            response = process_mpesa_payment(
                phone_number=phone_number,
                amount=amount,
                account_reference=f"WITHDRAW-{withdrawal.id}"
            )
            
            if response.get('ResponseCode') == '0':
                messages.success(request, "Withdrawal initiated. Please check your phone.")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Check your phone to complete withdrawal'
                })
            else:
                withdrawal.status = 'FAILED'
                withdrawal.save()
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to initiate withdrawal'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def update_delivery_status(request, order_id):
    if not hasattr(request.user, 'bodarider'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'})
        
    order = get_object_or_404(Order, id=order_id, assigned_rider=request.user.bodarider)
    status = request.POST.get('status')
    
    if status == 'PICKED_UP':
        order.delivery_status = 'PICKED_UP'
        order.save()
    elif status == 'DELIVERED':
        DeliveryAllocationService.complete_delivery(order)
    
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if not product.has_sufficient_stock(quantity):
            messages.error(request, 'Not enough stock available.')
            return redirect('connect:productdetails', id=product_id)
        
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            new_quantity = cart_item.quantity + quantity
            if not product.has_sufficient_stock(new_quantity):
                messages.error(request, 'Not enough stock available.')
                return redirect('connect:productdetails', id=product_id)
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        messages.success(request, f"{product.name} added to cart successfully!")
        return redirect('connect:cart')
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('connect:marketplacehome')
    except ValueError:
        messages.error(request, 'Invalid quantity specified.')
        return redirect('connect:productdetails', id=product_id)

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('connect:cart')

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
    return redirect('connect:cart')

@login_required
def confirm_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    if request.method == 'POST':
        notes = request.POST.get('notes')
        order.confirm_delivery(notes)
        messages.success(request, "Delivery confirmed successfully!")
        return redirect('connect:order_details', order_id=order.id)
    return render(request, 'connect/confirm_delivery.html', {'order': order})

@login_required
def confirm_payment(request, order_id):
    # Get the seller's products in this order
    order = get_object_or_404(Order, products__seller__user=request.user, id=order_id)
    if request.method == 'POST':
        notes = request.POST.get('notes')
        order.confirm_payment(notes)
        messages.success(request, "Payment confirmed successfully!")
        return redirect('connect:order_confirmation', order_id=order.id)
    return render(request, 'connect/confirm_payment.html', {'order': order})

@login_required
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_rider=request.user.bodarider)
    if request.method == 'POST':
        notes = request.POST.get('notes')
        order.delivery_status = 'DELIVERED'
        order.rider_notes = notes
        order.save()
        
        # Notify buyer
        Notification.objects.create(
            user=order.buyer,
            message=f"Your order #{order.id} has been delivered. Please confirm receipt."
        )
        
        messages.success(request, "Order marked as delivered!")
        return redirect('connect:rider_dashboard')
    return render(request, 'connect/mark_delivered.html', {'order': order})

@staff_member_required
def add_article(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        
        article = Article.objects.create(
            title=title,
            content=content,
            category=category,
            author=request.user,
            image=image
        )
        
        messages.success(request, "Article added successfully!")
        return redirect('connect:learninghub')
        
    categories = Category.objects.all()
    return render(request, 'connect/admin/add_article.html', {
        'categories': categories
    })

@staff_member_required
def add_course(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        duration = request.POST.get('duration')
        level = request.POST.get('level')
        instructor = request.POST.get('instructor')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        
        course = Course.objects.create(
            title=title,
            description=description,
            category=category,
            duration=duration,
            level=level,
            instructor=instructor,
            image=image
        )
        
        messages.success(request, "Course added successfully!")
        return redirect('connect:learninghub')
        
    categories = Category.objects.all()
    return render(request, 'connect/admin/add_course.html', {
        'categories': categories
    })

@staff_member_required
def admin_dashboard(request):
    # User Statistics
    total_users = User.objects.count()
    total_sellers = Seller.objects.count()
    total_buyers = Buyer.objects.count()
    total_riders = BodaRider.objects.count()
    
    # Learning Hub Statistics
    total_courses = Course.objects.count()
    total_articles = Article.objects.count()
    total_enrollments = CourseEnrollment.objects.count()
    
    # Marketplace Statistics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_earnings = Order.objects.filter(payment_status='COMPLETED').aggregate(
        total=models.Sum('total_price')
    )['total'] or 0
    
    context = {
        # User Stats
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_buyers': total_buyers,
        'total_riders': total_riders,
        
        # Learning Hub Stats
        'total_courses': total_courses,
        'total_articles': total_articles,
        'total_enrollments': total_enrollments,
        
        # Marketplace Stats
        'total_products': total_products,
        'total_orders': total_orders,
        'total_earnings': total_earnings,
    }
    
    return render(request, 'connect/admin/dashboard.html', context)

@login_required
def edit_discussion(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    
    # Check if user is author or admin
    if not (request.user == discussion.user or request.user.is_staff):
        messages.error(request, "You don't have permission to edit this discussion.")
        return redirect('connect:community_home')
    
    if request.method == 'POST':
        form = DiscussionForm(request.POST, instance=discussion)
        if form.is_valid():
            form.save()
            
            # Handle tags
            tags_input = request.POST.get('tagsList', '')
            discussion.tags.clear()  # Remove existing tags
            if tags_input:
                tag_names = tags_input.split(',')
                for tag_name in tag_names:
                    if tag_name.strip():
                        tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                        discussion.tags.add(tag)
            
            messages.success(request, "Discussion updated successfully!")
            return redirect('connect:community_home')
    else:
        form = DiscussionForm(instance=discussion)
    
    return render(request, 'connect/edit_discussion.html', {
        'form': form,
        'discussion': discussion
    })

@login_required
def delete_discussion(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    
    # Check if user is author or admin
    if not (request.user == discussion.user or request.user.is_staff):
        messages.error(request, "You don't have permission to delete this discussion.")
        return redirect('connect:community_home')
    
    if request.method == 'POST':
        discussion.delete()
        messages.success(request, "Discussion deleted successfully!")
        return redirect('connect:community_home')
    
    return render(request, 'connect/delete_discussion.html', {
        'discussion': discussion
    })

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'count': post.like_count()
    })

@login_required
def initiate_stk_push(request):
    if request.method == 'POST':
        try:
            phone_number = request.POST.get('mpesa_phone')
            amount = request.POST.get('amount')
            
            if not phone_number or not amount:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone number and amount are required'
                })
            
            response = process_mpesa_payment(
                phone_number=phone_number,
                amount=float(amount),
                account_reference=f"ORDER-{request.user.id}"
            )
            
            if response.get('ResponseCode') == '0':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Please check your phone to complete payment'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': response.get('ResponseDescription', 'Payment initiation failed')
                })
                
        except ValueError as e:
            logger.error(f"STK Push Error: Invalid amount format - {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid amount format'
            })
        except Exception as e:
            logger.error(f"STK Push Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def leave_testimonial(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        content = request.POST.get('content')

        # Create a new testimonial
        Testimonial.objects.create(name=name, content=content)

        messages.success(request, 'Thank you for your testimonial!')
        return redirect('connect:contact')  # Redirect back to contact page

    return redirect('connect:contact')  # Redirect if not a POST request

@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        phone_number = request.POST.get('mpesa_phone')

        # Process M-Pesa payment with the total amount
        response = process_mpesa_payment(
            phone_number=phone_number,
            amount=order.total_price,
            account_reference=f"ORDER-{order.id}"
        )

        # Check the response and handle accordingly
        if response.get('ResponseCode') == '0':
            messages.success(request, "Please check your phone to complete payment.")
            return redirect('connect:order_confirmation', order_id=order.id)
        else:
            messages.error(request, response.get('ResponseDescription', 'Payment initiation failed'))
            return redirect('connect:payment', order_id=order.id)

    return render(request, 'connect/payment.html', {
        'order': order,
    })
from django.shortcuts import render
from django.contrib.auth.models import User

def admin_user_list(request):
    users = User.objects.all()
    return render(request, 'admin_user_list.html', {'users': users})

def admin_product_list(request):
    products = Product.objects.all()
    return render(request, 'admin_product_list.html', {'products': products})
def admin_order_list(request):
    orders = Order.objects.all()
    return render(request, 'admin_order_list.html', {'orders': orders})
def admin_earnings(request):
    earnings = DeliveryEarning.objects.all()  # Using the correct model name
    return render(request, 'admin_earnings.html', {'earnings': earnings})

@login_required
def toggle_rider_availability(request):
    if not hasattr(request.user, 'bodarider'):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'})
    
    rider = request.user.bodarider
    new_status = request.POST.get('status')
    
    if new_status in ['Available', 'Offline']:
        rider.status = new_status
        rider.save()
        return JsonResponse({
            'status': 'success',
            'new_status': rider.status,
            'message': f'Status updated to {rider.status}'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid status'})

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            parent_id = data.get('parent_id')
            
            post = get_object_or_404(Post, id=post_id)
            
            # Create the comment
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent_id=parent_id
            )
            
            # Create notification for post author
            if request.user != post.author:
                Notification.objects.create(
                    user=post.author,
                    message=f"{request.user.get_full_name()} commented on your post"
                )
            
            # If this is a reply, notify the parent comment author
            if parent_id and comment.parent.author != request.user:
                Notification.objects.create(
                    user=comment.parent.author,
                    message=f"{request.user.get_full_name()} replied to your comment"
                )
            
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': naturaltime(comment.created_at),
                    'author': {
                        'username': comment.author.username,
                        'full_name': comment.author.get_full_name(),
                        'profile_picture': comment.author.profile.profile_picture.url if comment.author.profile.profile_picture else None
                    },
                    'likes_count': comment.likes.count(),
                    'is_liked': comment.is_liked_by_user(request.user),
                    'parent_id': comment.parent_id,
                    'post_id': post.id
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def toggle_reaction(request, post_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reaction_type = data.get('reaction_type')
            
            post = get_object_or_404(Post, id=post_id)
            reaction, created = PostReaction.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'reaction_type': reaction_type}
            )
            
            if not created:
                if reaction.reaction_type == reaction_type:
                    reaction.delete()
                    action = 'removed'
                else:
                    reaction.reaction_type = reaction_type
                    reaction.save()
                    action = 'changed'
            else:
                action = 'added'
                # Create notification for post author
                if request.user != post.author:
                    Notification.objects.create(
                        user=post.author,
                        message=f"{request.user.get_full_name()} reacted to your post"
                    )
            
            return JsonResponse({
                'status': 'success',
                'action': action,
                'reactions': post.get_reaction_counts()
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def toggle_follow(request, user_id):
    if request.method == 'POST':
        try:
            user_to_follow = get_object_or_404(User, id=user_id)
            
            if user_to_follow == request.user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You cannot follow yourself'
                })
            
            if request.user in user_to_follow.profile.followers.all():
                user_to_follow.profile.followers.remove(request.user)
                is_following = False
                # Remove notification
                Notification.objects.filter(
                    user=user_to_follow,
                    message__contains=f"{request.user.get_full_name()} started following you"
                ).delete()
            else:
                user_to_follow.profile.followers.add(request.user)
                is_following = True
                # Create notification
                Notification.objects.create(
                    user=user_to_follow,
                    message=f"{request.user.get_full_name()} started following you"
                )
            
            return JsonResponse({
                'status': 'success',
                'is_following': is_following,
                'followers_count': user_to_follow.profile.get_followers_count()
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def like_comment(request, comment_id):
    if request.method == 'POST':
        try:
            comment = get_object_or_404(Comment, id=comment_id)
            
            if request.user in comment.likes.all():
                comment.likes.remove(request.user)
                action = 'removed'
            else:
                comment.likes.add(request.user)
                action = 'added'
                # Create notification
                if request.user != comment.author:
                    Notification.objects.create(
                        user=comment.author,
                        message=f"{request.user.get_full_name()} liked your comment"
                    )
            
            return JsonResponse({
                'status': 'success',
                'action': action,
                'likes_count': comment.get_likes_count()
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent__isnull=True).prefetch_related('replies', 'author__profile')
    
    # Get similar posts based on hashtags
    similar_posts = Post.objects.filter(
        hashtags__in=post.hashtags.all()
    ).exclude(id=post.id).distinct()[:3]
    
    context = {
        'post': post,
        'comments': comments,
        'similar_posts': similar_posts,
        'user_reaction': post.get_user_reaction(request.user),
        'reaction_counts': post.get_reaction_counts()
    }
    return render(request, 'connect/community/post_detail.html', context)

@login_required
def group_join_request(request, group_id):
    if request.method == 'POST':
        try:
            group = get_object_or_404(Group, id=group_id)
            
            # Check if user is already a member
            if group.is_member(request.user):
                return JsonResponse({
                    'status': 'error',
                    'message': 'You are already a member of this group'
                })
            
            # Check if request already exists
            existing_request = GroupJoinRequest.objects.filter(
                user=request.user,
                group=group,
                status='PENDING'
            ).exists()
            
            if existing_request:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Join request already pending'
                })
            
            # Create new join request
            GroupJoinRequest.objects.create(
                user=request.user,
                group=group
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Join request sent successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def handle_join_request(request, request_id):
    if request.method == 'POST':
        try:
            join_request = get_object_or_404(
                GroupJoinRequest,
                id=request_id,
                group__admin=request.user  # Ensure user is group admin
            )
            
            action = request.POST.get('action')
            if action not in ['accept', 'reject']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid action'
                })
            
            join_request.status = 'ACCEPTED' if action == 'accept' else 'REJECTED'
            join_request.save()  # This will trigger the signal handler
            
            return JsonResponse({
                'status': 'success',
                'message': f'Request {action}ed successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
@require_POST
def create_product_review(request, product_id):
    try:
        order_id = request.POST.get('order_id')
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        ReviewService.create_product_review(
            product_id=product_id,
            buyer_id=request.user.id,
            order_id=order_id,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, "Review added successfully!")
        return JsonResponse({'status': 'success'})
        
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An error occurred'})

@login_required
@require_POST
def create_seller_review(request, seller_id):
    try:
        order_id = request.POST.get('order_id')
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        ReviewService.create_seller_review(
            seller_id=seller_id,
            buyer_id=request.user.id,
            order_id=order_id,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, "Review added successfully!")
        return JsonResponse({'status': 'success'})
        
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'An error occurred'})

def get_product_reviews(request, product_id):
    cursor_id = request.GET.get('cursor')
    reviews = ReviewService.get_product_reviews(
        product_id=product_id,
        cursor_id=cursor_id,
        limit=10
    )
    return JsonResponse({'reviews': reviews})

def get_seller_reviews(request, seller_id):
    cursor_id = request.GET.get('cursor')
    reviews = ReviewService.get_seller_reviews(
        seller_id=seller_id,
        cursor_id=cursor_id,
        limit=10
    )
    return JsonResponse({'reviews': reviews})

def courses_list(request):
    courses = Course.objects.all().order_by('-created_at')
    context = {
        'courses': courses,
        'page_title': 'Available Courses'
    }
    return render(request, 'connect/courses_list.html', context)

def resources_list(request):
    resources = Resource.objects.all().order_by('-created_at')
    context = {
        'resources': resources,
        'page_title': 'Learning Resources'
    }
    return render(request, 'connect/resources_list.html', context)

@login_required
def learning_progress(request):
    user_progress = UserProgress.objects.filter(user=request.user)
    context = {
        'progress': user_progress,
        'page_title': 'My Learning Progress'
    }
    return render(request, 'connect/learning_progress.html', context)

def community_home(request):
    context = {
        'page_title': 'Learning Community'
    }
    return render(request, 'connect/community_home.html', context)

def marketplace_home(request):
    # Debug query execution
    products = Product.objects.all()
    logger.debug(f"Total products found: {products.count()}")
    
    # Debug individual products
    for product in products:
        logger.debug(f"Product ID: {product.id}, Name: {product.name}, Seller: {product.seller.company_name}")
    
    context = {
        'products': products,
        'categories': Category.objects.all(),
    }
    return render(request, 'connect/marketplace.html', context)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'productlist.html', {'products': products})


def debug_database(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        # Test database connection
        with connection.cursor() as cursor:
            # Check products table
            cursor.execute("""
                SELECT COUNT(*) FROM connect_product;
            """)
            product_count = cursor.fetchone()[0]
            
            # Get the last 5 products
            cursor.execute("""
                SELECT id, name, created_at 
                FROM connect_product 
                ORDER BY created_at DESC 
                LIMIT 5;
            """)
            recent_products = cursor.fetchall()
            
            # Check seller relationships
            cursor.execute("""
                SELECT p.id, p.name, s.company_name 
                FROM connect_product p
                JOIN connect_seller s ON p.seller_id = s.id
                LIMIT 5;
            """)
            seller_products = cursor.fetchall()
            
        return JsonResponse({
            'status': 'success',
            'product_count': product_count,
            'recent_products': recent_products,
            'seller_products': seller_products
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })