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
    User, CourseEnrollment, Article, Wishlist, Withdrawal
)
from .forms import (
    CustomUserCreationForm, DiscussionForm, PostForm,
    SellerProfileForm, BuyerProfileForm, BodaRiderProfileForm
)
from .mpesa import initiate_stk_push
from .services import DeliveryAllocationService
import json

def home(request):
    return render(request, 'connect/home.html')

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
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
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
            
        return redirect('connect:contact')
    
    return render(request, 'connect/contact.html')

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

def home(request):
    # Get active testimonials
    testimonials = Testimonial.objects.filter(is_active=True)[:3]  # Show only 3 testimonials
    return render(request, 'connect/home.html', {'testimonials': testimonials})
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

def coursedetails(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    comments = course.comments.all()
    if request.method == "POST":
        comment_text = request.POST.get('comment')
        if comment_text:
            Comment.objects.create(user=request.user, course=course, text=comment_text)
    return render(request, 'coursedetails.html', {'course': course, 'lessons': lessons, 'comments': comments})


# View for the community home page
def communityhome(request):
    tag_filter = request.GET.get('tag')
    search_query = request.GET.get('query')

    discussions = Discussion.objects.all().order_by('-created_at')
    tags = Tag.objects.all()

    if tag_filter:
        discussions = discussions.filter(tags__name=tag_filter)
    
    if search_query:
        discussions = discussions.filter(title__icontains=search_query)
    
    return render(request, 'connect/communityhome.html', {
        'discussions': discussions,
        'tags': tags,
        'tag_filter': tag_filter,
        'search_query': search_query
    })

# View for discussion details and posts
def discussiondetails(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    posts = discussion.posts.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.discussion = discussion
            post.save()
            return redirect('discussiondetails', discussion_id=discussion.id)
    else:
        form = PostForm()
    
    return render(request, 'discussiondetails.html', {
        'discussion': discussion,
        'posts': posts,
        'form': form,
    })

# View for creating a new discussion
@login_required
def creatediscussion(request):
    if request.method == 'POST':
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.user = request.user
            discussion.save()
            form.save_m2m()  # Save the many-to-many tags
            return redirect('connect:communityhome')
    else:
        form = DiscussionForm()
    
    return render(request, 'connect/creatediscussion.html', {
        'form': form
    })

# View for searching discussions
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
    return render(request, 'productdetails.html', {'product': product})

# 3. Cart
def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

# 4. Checkout
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('connect:marketplacehome')
    
    if request.method == 'POST':
        try:
            delivery_address = request.POST.get('delivery_address')
            delivery_instructions = request.POST.get('delivery_instructions')
            contact_number = request.POST.get('contact_number')
            
            if not delivery_address or not contact_number:
                messages.error(request, "Delivery address and contact number are required.")
                return redirect('connect:checkout')
            
            # Calculate total price
            total_price = sum(item.product.price * item.quantity for item in cart_items)
            
            # Create order
            order = Order.objects.create(
                buyer=request.user,
                total_price=total_price,
                delivery_address=delivery_address,
                delivery_instructions=delivery_instructions,
                contact_number=contact_number,
                status='Pending',
                delivery_status='PENDING'
            )
            
            # Add order items
            for item in cart_items:
                if item.product.stock < item.quantity:
                    messages.error(request, f"Not enough stock for {item.product.name}")
                    order.delete()
                    return redirect('connect:checkout')
                    
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity
                )
                
                # Update product stock
                item.product.stock -= item.quantity
                item.product.save()
            
            # Try to assign a rider
            if DeliveryAllocationService.assign_rider(order):
                messages.success(request, "Order placed successfully! A rider has been assigned.")
            else:
                messages.warning(request, "Order placed but no riders are currently available. We'll assign one soon.")
            
            # Clear cart
            cart_items.delete()
            
            return redirect('connect:orderconfirmation', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"Error processing order: {str(e)}")
            return redirect('connect:checkout')
    
    context = {
        'cart_items': cart_items,
        'total_price': sum(item.product.price * item.quantity for item in cart_items)
    }
    return render(request, 'connect/checkout.html', context)

# 5. Order Confirmation
def orderconfirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orderconfirmation.html', {'order': order})

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
        product = Product.objects.create(
            seller=request.user.seller,
            name=request.POST['name'],
            description=request.POST['description'],
            price=request.POST['price'],
            stock=request.POST['stock'],
        )
        return redirect('connect:productdetails', id=product.id)
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
def negotiationchats(request):
    negotiations = Negotiation.objects.filter(user=request.user)
    return render(request, 'negotiationchats.html', {'negotiations': negotiations})

# 13. Wishlist
def wishlist(request):
    user = request.user
    wishlist_items = Wishlist.objects.filter(user=user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

# 14. Delivery Tracking
def deliverytracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'deliverytracking.html', {'order': order})

# 15. Chatbox (All Chats)
def chatbox(request):
    chats = Chat.objects.filter(user=request.user)  # Assuming the user has related chats
    return render(request, 'chatbox.html', {'chats': chats})

# 16. Chatbox Frame (Specific Chat)
def chatboxframe(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    messages = chat.messages.all()
    if request.method == 'POST':
        message = request.POST['message']
        chat.messages.create(user=request.user, content=message)
    return render(request, 'chatboxframe.html', {'chat': chat, 'messages': messages})

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
        wishlist_items = Wishlist.objects.filter(user=request.user)
        cart_items = Cart.objects.filter(user=request.user)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        
        context = {
            'buyer': buyer,
            'orders': orders,
            'total_orders': orders.count(),
            'pending_orders': orders.filter(status='Pending').count(),
            'completed_orders': orders.filter(status='Completed').count(),
            'wishlist_items': wishlist_items,
            'cart_items': cart_items,
            'cart_total': cart_total,
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
                ['your.email@gmail.com'],  # Replace with your email where you want to receive messages
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
            response = initiate_stk_push(
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
    if request.method == 'POST':
        try:
            response = json.loads(request.body)
            ref_number = response.get('BillRefNumber', '')
            
            if ref_number.startswith('ORDER-'):
                # Handle order payment
                order_id = ref_number.split('-')[1]
                order = Order.objects.get(id=order_id)
                
                if response.get('ResultCode') == 0:
                    order.payment_status = 'COMPLETED'
                    order.mpesa_transaction_id = response.get('MpesaReceiptNumber')
                    order.save()
                    
                    if order.assigned_rider:
                        DeliveryEarning.objects.create(
                            rider=order.assigned_rider,
                            order=order,
                            amount=order.delivery_fee,
                            paid=False
                        )
                    return JsonResponse({'status': 'success'})
                    
            elif ref_number.startswith('WITHDRAW-'):
                # Handle withdrawal
                withdrawal_id = ref_number.split('-')[1]
                withdrawal = Withdrawal.objects.get(id=withdrawal_id)
                
                if response.get('ResultCode') == 0:
                    withdrawal.status = 'COMPLETED'
                    withdrawal.transaction_id = response.get('MpesaReceiptNumber')
                    withdrawal.save()
                    
                    # Mark earnings as paid
                    earnings = DeliveryEarning.objects.filter(
                        rider=withdrawal.rider,
                        paid=False
                    )
                    remaining = withdrawal.amount
                    for earning in earnings:
                        if remaining <= 0:
                            break
                        if earning.amount <= remaining:
                            earning.paid = True
                            earning.save()
                            remaining -= earning.amount
                        else:
                            # Split the earning if needed
                            paid_part = DeliveryEarning.objects.create(
                                rider=earning.rider,
                                order=earning.order,
                                amount=remaining,
                                paid=True
                            )
                            earning.amount -= remaining
                            earning.save()
                            remaining = 0
                    
                    return JsonResponse({'status': 'success'})
                else:
                    withdrawal.status = 'FAILED'
                    withdrawal.save()
            
            return JsonResponse({'status': 'failed'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

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
            response = initiate_stk_push(
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
