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
from django.db.models import Q
from django.db import models
from .models import (
    Product, Order, Seller, BodaRider, Buyer,
    DeliveryEarning, OrderItem, Cart, Testimonial,
    Discussion, Post, Tag, Category, Course, Comment,
    User, CourseEnrollment, Article, Wishlist, Withdrawal,
    DeliveryAddress, Notification, Negotiation, Chat, Message
)
from .forms import (
    CustomUserCreationForm, DiscussionForm, PostForm,
    SellerProfileForm, BuyerProfileForm, BodaRiderProfileForm,ContactForm
)
from .mpesa import initiate_stk_push as process_mpesa_payment
from .services import DeliveryAllocationService
import json
from django.contrib.admin.views.decorators import staff_member_required
import logging
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

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

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
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
                send_mail(
                    email_subject,
                    email_message,
                    settings.EMAIL_HOST_USER,
                    ['nzau878@gmail.com'],  
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message! We will get back to you soon.')
            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')

            return redirect(reverse('connect:contact'))

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
def communityhome(request):
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
    
    return render(request, 'connect/communityhome.html', {
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
            return redirect('connect:communityhome')
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
def marketplacehome(request):
    # Get all products
    products = Product.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'search_query': search_query,
        'selected_category': category_id,
    }
    
    return render(request, 'connect/marketplacehome.html', context)

# 2. Product Details
def productdetails(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'connect/productdetails.html', {'product': product})

# 3. Cart
def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    
    # Calculate subtotal for each item
    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
    
    total_price = sum(item.subtotal for item in cart_items)
    return render(request, 'connect/cart.html', {'cart_items': cart_items, 'total_price': total_price})

# 4. Checkout
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)  # Get cart items for the user
    total_cost = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method')
        delivery_fee = 0

        if delivery_method == 'Boda Rider':
            delivery_fee = 50  # Base fee for boda rider

        # Create the order
        order = Order.objects.create(
            buyer=request.user,
            delivery_method=delivery_method,
            delivery_fee=delivery_fee,
            total_price=total_cost + delivery_fee  # Total cost including delivery fee
        )

        # Set the seller based on the products in the cart
        sellers = set(item.product.seller for item in cart_items)  # Assuming Product has a seller field
        if sellers:
            order.seller = sellers.pop()  # Assign the first seller found
            order.save()

        # Redirect to payment processing (M-Pesa STK Push)
        return redirect('connect:payment', order_id=order.id)

    return render(request, 'connect/checkout.html', {
        'cart_items': cart_items,
        'total_cost': total_cost,
    })

# 5. Order Confirmation
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'connect/order_confirmation.html', {
        'order': order,
    })

# 6. Buyer Orders
def buyerorders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'buyerorders.html', {'orders': orders})

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

# 9. Add Product (Seller)
def addproduct(request):
    if request.method == 'POST':
        seller = request.user.seller
        if not seller.location:
            messages.error(request, "Seller location is required.")
            return redirect('connect:addproduct')

        try:
            # Validate image
            image = request.FILES.get('image')
            if image:
                # Check file size (5MB limit)
                if image.size > 5 * 1024 * 1024:
                    messages.error(request, "Image file is too large ( > 5MB )")
                    return redirect('connect:addproduct')
                
                # Check file type
                allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
                if image.content_type not in allowed_types:
                    messages.error(request, "Only JPEG and PNG images are allowed")
                    return redirect('connect:addproduct')

            product = Product.objects.create(
                seller=seller,
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                stock=request.POST['stock'],
                unit=request.POST.get('unit', 'kg'),
                location=request.POST.get('location', seller.location),
                delivery_available='delivery_available' in request.POST,
                pickup_available='pickup_available' in request.POST,
                image=image if image else None
            )

            messages.success(request, "Product added successfully!")
            return redirect('connect:productdetails', id=product.id)
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
            return redirect('connect:addproduct')

    return render(request, 'connect/addproduct.html')

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
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect based on user type
            if hasattr(user, 'seller'):
                return redirect('connect:sellerdashboard')
            elif hasattr(user, 'buyer'):
                return redirect('connect:buyerdashboard')
            elif hasattr(user, 'bodarider'):
                return redirect('connect:bodariderdashboard')
            return redirect('connect:home')
    else:
        form = AuthenticationForm()

    return render(request, 'connect/login.html', {'form': form})


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
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        # Check if product is already in cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        # If product was already in cart, update quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f"{product.name} added to cart successfully!")
        return redirect('connect:cart')
    
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
        return redirect('connect:communityhome')
    
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
            return redirect('connect:communityhome')
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
        return redirect('connect:communityhome')
    
    if request.method == 'POST':
        discussion.delete()
        messages.success(request, "Discussion deleted successfully!")
        return redirect('connect:communityhome')
    
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
    earnings = Earnings.objects.all()  # Customize the query as needed
    return render(request, 'admin_earnings.html', {'earnings': earnings})