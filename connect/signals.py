from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, Cart, Order, Notification

# Signal to update product stock after an order is placed
@receiver(post_save, sender=Order)
def update_product_stock(sender, instance, created, **kwargs):
    if created:
        for product in instance.products.all():
            product.stock -= product.quantity
            product.save()

# Signal to send a notification when a new product is added to the cart
@receiver(post_save, sender=Cart)
def cart_added_notification(sender, instance, created, **kwargs):
    if created:
        # Send a notification to the buyer
        Notification.objects.create(
            user=instance.user,
            message=f"Product {instance.product.name} has been added to your cart."
        )

# Signal to create a notification when a new order is placed
@receiver(post_save, sender=Order)
def order_placed_notification(sender, instance, created, **kwargs):
    if created:
        # Notify the buyer and seller
        Notification.objects.create(
            user=instance.buyer,
            message=f"Your order for {instance.total_price} has been placed successfully."
        )
        Notification.objects.create(
            user=instance.seller,
            message=f"You have received a new order from {instance.buyer.username}."
        )

# Signal to send an email when a product is added
@receiver(post_save, sender=Product)
def send_product_add_email(sender, instance, created, **kwargs):
    if created:
        # Send a notification email to the seller or admin
        send_mail(
            'New Product Added',
            f"A new product '{instance.name}' has been added to the marketplace.",
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL]
        )
