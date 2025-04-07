from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import html
from urllib.parse import parse_qs
from django.core.exceptions import ValidationError

def handle_file_upload(request):
    uploaded_file = request.FILES['file']
    


def my_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('mpesa_phone')
        # Process the phone number...

# Base models
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/')
    criteria = models.JSONField()  # Store criteria for earning badge
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Community Models
class CommunityGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='joined_groups')
    moderators = models.ManyToManyField(User, related_name='moderated_groups')
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name}"

    def get_posts_count(self):
        return self.posts.count()

class CommunityPost(models.Model):
    REACTION_CHOICES = [
        ('LIKE', '👍'),
        ('LOVE', '❤️'),
        ('INSIGHTFUL', '💡'),
        ('SUPPORT', '🤝'),
    ]

    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('NONE', 'None')
    ]

    CATEGORY_CHOICES = [
        ('CROP_FARMING', 'Crop Farming'),
        ('LIVESTOCK_FARMING', 'Livestock Farming'),
        ('ORGANIC_FARMING', 'Organic Farming'),
        ('AQUACULTURE', 'Aquaculture'),
        ('AGROFORESTRY', 'Agroforestry'),
        ('HORTICULTURE', 'Horticulture'),
        ('APICULTURE', 'Apiculture'),
        ('AGRIBUSINESS', 'Agribusiness'),
        ('AGRICULTURAL_TECHNOLOGY', 'Agricultural Technology'),
        ('CLIMATE_SMART_AGRICULTURE', 'Climate-Smart Agriculture'),
        ('PERMACULTURE', 'Permaculture'),
        ('SOIL_WATER_MANAGEMENT', 'Soil & Water Management'),
        ('IRRIGATION_SYSTEMS', 'Irrigation Systems'),
        ('AGRICULTURAL_POLICY', 'Agricultural Policy'),
        ('POST_HARVEST_MANAGEMENT', 'Post-Harvest Management'),
        ('AGROECOLOGY', 'Agroecology'),
        ('FARM_MACHINERY_TOOLS', 'Farm Machinery & Tools'),
        ('GREENHOUSE_FARMING', 'Greenhouse Farming'),
        ('POULTRY_FARMING', 'Poultry Farming'),
        ('DAIRY_FARMING', 'Dairy Farming'),
        ('FISHERIES', 'Fisheries'),
        ('ANIMAL_HEALTH', 'Animal Health'),
        ('AGROCHEMICALS_FERTILIZERS', 'Agrochemicals & Fertilizers'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    categories = models.JSONField(default=list)  # Store multiple categories
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='NONE')
    media = models.FileField(upload_to='post_media/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hashtags = models.ManyToManyField('Hashtag', blank=True, related_name='posts')
    group = models.ForeignKey('CommunityGroup', on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    def __str__(self):
        return f"{self.title} by {self.author.username}"

    def get_comments_count(self):
        return self.comments.count()

    def get_reactions_count(self):
        return self.reactions.count()

    def get_reaction_counts(self):
        counts = {}
        for reaction_type, _ in self.REACTION_CHOICES:
            counts[reaction_type] = self.reactions.filter(reaction_type=reaction_type).count()
        return counts

    def get_user_reaction(self, user):
        if not user.is_authenticated:
            return None
        reaction = self.reactions.filter(user=user).first()
        return reaction.reaction_type if reaction else None

class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"

    def get_replies_count(self):
        return self.replies.count()

    def get_likes_count(self):
        return self.likes.count()

    def is_liked_by_user(self, user):
        return self.likes.filter(id=user.id).exists()

class Course(models.Model):
    LEVEL_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='courses/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='BEGINNER')
    duration = models.CharField(max_length=50, help_text="e.g., '2 hours', '4 weeks'")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['level']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def get_enrolled_count(self):
        return self.enrollments.count()

    def get_completion_rate(self):
        total = self.enrollments.count()
        if total == 0:
            return 0
        completed = self.enrollments.filter(completed=True).count()
        return (completed / total) * 100

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title

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
        help_text="Check if you offer personal delivery service"
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Delivery fee if you offer delivery service"
    )
    farm_pickup = models.BooleanField(
        default=True,
        help_text="Allow customers to pick up from your farm"
    )
    farm_pickup_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Instructions for farm pickup (directions, timing, etc.)"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def get_delivery_options(self):
        options = []
        if self.farm_pickup:
            options.append({
                'type': 'FARM_PICKUP',
                'name': 'Farm Pickup',
                'fee': 0,
                'instructions': self.farm_pickup_instructions
            })
        if self.delivery_available:
            options.append({
                'type': 'PERSONAL_DELIVERY',
                'name': 'Personal Delivery',
                'fee': self.delivery_fee,
                'instructions': None
            })
        return options

    def clean(self):
        if self.price < 0:
            raise ValidationError('Price cannot be negative')
        if self.stock < 0:
            raise ValidationError('Stock cannot be negative')

    def has_sufficient_stock(self, quantity):
        return self.stock >= quantity

    def update_stock(self, quantity_change):
        if self.stock + quantity_change < 0:
            raise ValidationError('Insufficient stock')
        self.stock += quantity_change
        self.save()

    def get_formatted_price(self):
        return f"KES {self.price:,.2f}"

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price']),
            models.Index(fields=['location']),
            models.Index(fields=['stock']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category']),
        ]

    def save(self, *args, **kwargs):
        # Ensure category exists
        if not self.category_id:
            default_category, _ = Category.objects.get_or_create(
                name='Uncategorized',
                defaults={'description': 'Default category for uncategorized products'}
            )
            self.category = default_category
        super().save(*args, **kwargs)

class Order(models.Model):
    DELIVERY_METHOD_CHOICES = [
        ('PERSONAL_DELIVERY', 'Personal Delivery'),
        ('FARM_PICKUP', 'Farm Pickup'),
    ]
    
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
        ('FAILED', 'Payment Failed')
    ]
    
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True, null=True)
    payment_notes = models.TextField(blank=True, null=True)
    rider_notes = models.TextField(blank=True, null=True)
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        default='FARM_PICKUP'
    )
    pickup_date = models.DateField(null=True, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)

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

class Discussion(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    tags = models.ManyToManyField(Tag, related_name='discussions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_posts')
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, through='PostLike', related_name='liked_posts', blank=True)

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
class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"

# User Profile Enhancement
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    followers = models.ManyToManyField(User, related_name='following', blank=True)
    website = models.URLField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.user.following.count()

class PostReaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=CommunityPost.REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']

    def __str__(self):
        return f"{self.user.username}'s {self.reaction_type} reaction on Post {self.post.id}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, null=True)
    attendees = models.ManyToManyField(User, related_name='attending_events')
    group = models.ForeignKey(CommunityGroup, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class LiveStream(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    streamer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streams')
    stream_key = models.CharField(max_length=100, unique=True)
    is_live = models.BooleanField(default=False)
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    viewers = models.ManyToManyField(User, related_name='watched_streams')
    group = models.ForeignKey(CommunityGroup, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Report(models.Model):
    REPORT_TYPES = [
        ('POST', 'Post'),
        ('COMMENT', 'Comment'),
        ('USER', 'User'),
        ('GROUP', 'Group'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    reported_post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, null=True, blank=True)
    reported_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    reported_group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Report by {self.reporter.username} - {self.report_type}"

class Poll(models.Model):
    post = models.OneToOneField(CommunityPost, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=200)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

    def get_total_votes(self):
        return sum(option.votes.count() for option in self.options.all())

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=100)
    votes = models.ManyToManyField(User, related_name='poll_votes')

    def __str__(self):
        return self.text

    def get_vote_count(self):
        return self.votes.count()

class UserBlock(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['blocker', 'blocked']

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_groups')
    members = models.ManyToManyField(User, related_name='member_groups')
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)

    def __str__(self):
        return self.name

    def get_member_count(self):
        return self.members.count()

    def is_member(self, user):
        return self.members.filter(id=user.id).exists()

    def is_admin(self, user):
        return self.admin == user

class GroupJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.group.name} ({self.status})"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('product', 'buyer', 'order')
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['buyer', 'created_at']),
        ]

class SellerReview(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('seller', 'buyer', 'order')
        indexes = [
            models.Index(fields=['seller', 'created_at']),
            models.Index(fields=['buyer', 'created_at']),
        ]

class Resource(models.Model):
    RESOURCE_TYPES = (
        ('PDF', 'PDF Document'),
        ('VIDEO', 'Video'),
        ('LINK', 'External Link'),
        ('DOC', 'Document')
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    progress_percentage = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username}'s progress in {self.course.title}"
