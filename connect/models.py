from django.db import models
from django.contrib.auth.models import User

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

class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
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
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    delivery_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    delivery_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # in kilometers
    base_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)  # Base fee
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # Rate per kilometer

    def __str__(self):
        return f"Order #{self.id}"

    def calculate_delivery_fee(self):
        if self.delivery_distance:
            return self.base_delivery_fee + (self.delivery_distance * self.per_km_rate)
        return self.base_delivery_fee

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
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)  # e.g., "Farmer", "Buyer", etc.
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 rating
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.name}"

    class Meta:
        ordering = ['-created_at']

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
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

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

    def __str__(self):
        return f'Post by {self.user.username} in {self.discussion.title}'

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


