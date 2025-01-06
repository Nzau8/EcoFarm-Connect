from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import html
from urllib.parse import parse_qs

def handle_file_upload(request):
    uploaded_file = request.FILES['file']
    


def my_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('mpesa_phone')
        # Process the phone number...

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="courses")
    duration = models.CharField(max_length=50)
    level = models.CharField(max_length=50, choices=[
        ("Beginner", "Beginner"), 
        ("Intermediate", "Intermediate"), 
        ("Advanced", "Advanced")
    ])
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    instructor = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.course.title}"

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.company_name

class DeliveryRating(models.Model):
    rider = models.ForeignKey('BodaRider', on_delete=models.CASCADE, related_name='ratings')
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['rider', 'order']

class BodaRider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bodarider')
    bike_model = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=[
        ('Available', 'Available'),
        ('On Delivery', 'On Delivery'),
        ('Offline', 'Offline')
    ], default='Available')

    def __str__(self):
        return f"{self.user.username}'s Boda Rider Profile"

    def get_rating(self):
        from django.db.models import Avg
        return DeliveryRating.objects.filter(rider=self).aggregate(Avg('rating'))['rating__avg'] or 0

class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('pcs', 'Pieces'),
        ('l', 'Litres'),
        ('ml', 'Millilitres'),
        ('bunch', 'Bunch'),
    ]
    
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    location = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_available = models.BooleanField(
        default=False,
        help_text="Check if you will handle delivery yourself. If unchecked, customers can select a rider."
    )
    pickup_available = models.BooleanField(
        default=True,
        help_text="Allow customers to pick up from your location"
    )

    def __str__(self):
        return self.name

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.CharField(max_length=255, blank=True, null=True)
    delivery_instructions = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    assigned_rider = models.ForeignKey(BodaRider, 
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     blank=True,
                                     related_name='deliveries')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    DELIVERY_STATUS_CHOICES = [
        ('PENDING', 'Pending Assignment'),
        ('ASSIGNED', 'Rider Assigned'),
        ('PICKED_UP', 'Picked Up'),
        ('DELIVERED', 'Delivered'),
        ('CONFIRMED', 'Delivery Confirmed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('INITIATED', 'Payment Initiated'),
        ('COMPLETED', 'Payment Completed'),
        ('CONFIRMED', 'Payment Confirmed'),
        ('FAILED', 'Payment Failed')
    ]
    
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True, null=True)
    payment_notes = models.TextField(blank=True, null=True)
    rider_notes = models.TextField(blank=True, null=True)
    delivery_method = models.CharField(max_length=50, default='Buyer')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Delivery fee

    def confirm_delivery(self, notes=None):
        self.delivery_status = 'CONFIRMED'
        self.delivery_confirmed_at = timezone.now()
        if notes:
            self.delivery_notes = notes
        self.save()
        # Send notifications
        self.notify_delivery_confirmation()

    def confirm_payment(self, notes=None):
        self.payment_status = 'CONFIRMED'
        self.payment_confirmed_at = timezone.now()
        if notes:
            self.payment_notes = notes
        self.save()
        # Send notifications
        self.notify_payment_confirmation()

    def notify_delivery_confirmation(self):
        # Notify seller and rider
        Notification.objects.create(
            user=self.get_primary_seller().user,
            message=f"Delivery confirmed for Order #{self.id}"
        )
        if self.assigned_rider:
            Notification.objects.create(
                user=self.assigned_rider.user,
                message=f"Delivery confirmed for Order #{self.id}"
            )

    def notify_payment_confirmation(self):
        # Notify buyer and rider
        Notification.objects.create(
            user=self.buyer,
            message=f"Payment confirmed for Order #{self.id}"
        )
        if self.assigned_rider:
            Notification.objects.create(
                user=self.assigned_rider.user,
                message=f"Payment confirmed for Order #{self.id}. You can collect your earnings."
            )

    def __str__(self):
        return f"Order #{self.id}"

    def calculate_delivery_fee(self):
        base_fee = 100.00  # Base delivery fee
        per_km_rate = 50.00  # Rate per kilometer
        if self.delivery_distance:
            return base_fee + (self.delivery_distance * per_km_rate)
        return base_fee

    def get_sellers(self):
        """Get all sellers associated with this order's products"""
        return Seller.objects.filter(product__orderitem__order=self).distinct()

    def get_primary_seller(self):
        """Get the first seller associated with this order"""
        sellers = self.get_sellers()
        return sellers.first() if sellers.exists() else None

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

class DeliveryEarning(models.Model):
    rider = models.ForeignKey(BodaRider, on_delete=models.CASCADE, related_name='earnings')
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Earning for Order #{self.order.id}"

class Testimonial(models.Model):
    USER_TYPE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('bodarider', 'Boda Rider'),
    ]

    name = models.CharField(max_length=100)
    content = models.TextField()
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='buyer')
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} in cart"

class Buyer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer')
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return f"{self.user.username}'s Buyer Profile"

class Chat(models.Model):
    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat with {', '.join([user.username for user in self.participants.all()])}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlists")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlists")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Ensure a user can't add the same product twice

    def __str__(self):
        return f"{self.user.username}'s wishlist - {self.product.name}"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Discussion(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    tags = models.ManyToManyField(Tag, related_name='discussions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, through='PostLike', related_name='liked_post_set', blank=True)

    def __str__(self):
        return f'Post by {self.user.username} in {self.discussion.title}'

    def like_count(self):
        return self.post_likes.count()

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

class Negotiation(models.Model):
    buyer = models.ForeignKey(User, related_name='buyer_negotiations', on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'), 
        ('Accepted', 'Accepted'), 
        ('Declined', 'Declined')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Negotiation for {self.product.name}"

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)  # 0-100%

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Withdrawal(models.Model):
    rider = models.ForeignKey(BodaRider, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Withdrawal of KES {self.amount} by {self.rider.user.username}"

class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_addresses')
    address_name = models.CharField(max_length=100)  # e.g., "Home", "Office"
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)
    delivery_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.address_name} - {self.address}"

    def save(self, *args, **kwargs):
        # If this address is being set as default, remove default from other addresses
        if self.is_default:
            DeliveryAddress.objects.filter(user=self.user).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


