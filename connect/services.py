from django.db.models import Q
from .models import BodaRider, Order, DeliveryEarning
from datetime import datetime

class DeliveryAllocationService:
    @staticmethod
    def find_available_rider(order):
        """Find the nearest available rider for an order"""
        try:
            delivery_location = order.delivery_address.split(',')[0].strip().lower()
            available_riders = BodaRider.objects.filter(
                status='Available'
            ).filter(
                Q(location__icontains=delivery_location) |
                Q(location__iexact=delivery_location)
            )
            
            if not available_riders.exists():
                # If no exact match, try broader search
                available_riders = BodaRider.objects.filter(status='Available')
            
            if available_riders.exists():
                return available_riders.first()
                
        except Exception as e:
            print(f"Error finding rider: {str(e)}")
        return None
    
    @staticmethod
    def assign_rider(order):
        try:
            # Get available riders
            available_riders = BodaRider.objects.filter(status='Available')
            
            if not available_riders.exists():
                return False
            
            # Get the seller's location from the first product in the order
            order_items = order.orderitem_set.select_related('product__seller').first()
            if not order_items:
                return False
                
            seller_location = order_items.product.seller.location
            
            # Try to find a rider in the same area first
            delivery_location = order.delivery_address.split(',')[0].strip().lower()
            nearby_riders = available_riders.filter(
                Q(location__icontains=delivery_location) |
                Q(location__iexact=delivery_location)
            )
            
            # If no nearby riders, use any available rider
            rider = nearby_riders.first() if nearby_riders.exists() else available_riders.first()
            
            # Assign rider and update statuses
            order.assigned_rider = rider
            order.delivery_status = 'ASSIGNED'
            order.save()
            
            rider.status = 'On Delivery'
            rider.save()
            
            return True
            
        except Exception as e:
            print(f"Error assigning rider: {str(e)}")
            return False
    
    @staticmethod
    def complete_delivery(order):
        """Mark a delivery as completed"""
        if order.assigned_rider:
            # Update order status
            order.delivery_status = 'DELIVERED'
            order.status = 'Completed'
            order.save()
            
            # Update rider status
            rider = order.assigned_rider
            rider.status = 'Available'
            rider.save()
            
            # Create delivery earnings
            DeliveryEarning.objects.create(
                rider=rider,
                order=order,
                amount=order.delivery_fee
            ) 