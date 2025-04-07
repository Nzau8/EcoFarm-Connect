from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Product, Cart, Order, Notification, UserProfile, GroupJoinRequest

# update product stock after an order is placed
@receiver(post_save, sender=Order)
def update_product_stock(sender, instance, created, **kwargs):
    if created:
        for product in instance.products.all():
            product.stock -= product.quantity
            product.save()

# send a notification when a new product is added to the cart
@receiver(post_save, sender=Cart)
def cart_added_notification(sender, instance, created, **kwargs):
    if created:
        # Send a notification to the buyer
        Notification.objects.create(
            user=instance.user,
            message=f"Product {instance.product.name} has been added to your cart."
        )

# create a notification when a new order is placed
@receiver(post_save, sender=Order)
def order_placed_notification(sender, instance, created, **kwargs):
    if created:
        # Notify the buyer
        Notification.objects.create(
            user=instance.buyer,
            message=f"Your order for {instance.total_price} has been placed successfully."
        )
        if instance.seller:
            Notification.objects.create(
                user=instance.seller.user,
                message=f"New order placed: #{instance.id}"
            )

# send an email when a product is added
@receiver(post_save, sender=Product)
def send_product_add_email(sender, instance, created, **kwargs):
    if created:
        # notification email to the seller or admin
        send_mail(
            'New Product Added',
            f"A new product '{instance.name}' has been added to the marketplace.",
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL]
        )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

# Custom signals
user_joined_group = Signal()
user_left_group = Signal()

@receiver(post_save, sender=GroupJoinRequest)
def handle_group_request_update(sender, instance, created, **kwargs):
    """Handle notifications when a group join request is created or updated"""
    if created:
        # Notify group admin of new request
        Notification.objects.create(
            user=instance.group.admin,
            message=f"{instance.user.get_full_name()} requested to join {instance.group.name}"
        )
    elif instance.status == 'ACCEPTED':
        # Add user to group members
        instance.group.members.add(instance.user)
        # Send notification to user
        Notification.objects.create(
            user=instance.user,
            message=f"Your request to join {instance.group.name} has been accepted"
        )
        # Emit custom signal
        user_joined_group.send(
            sender=sender,
            user=instance.user,
            group=instance.group
        )
    elif instance.status == 'REJECTED':
        # Send notification to user
        Notification.objects.create(
            user=instance.user,
            message=f"Your request to join {instance.group.name} has been rejected"
        )
