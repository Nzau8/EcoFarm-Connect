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
        """Assign a rider to an order"""
        rider = DeliveryAllocationService.find_available_rider(order)
        if rider:
            order.assigned_rider = rider
            order.delivery_status = 'ASSIGNED'
            order.delivery_fee = order.calculate_delivery_fee()
            order.save()
            
            # Update rider status
            rider.status = 'On Delivery'
            rider.save()
            
            return True
        return False
    
    @staticmethod
    def complete_delivery(order):
        """Mark a delivery as completed"""
        if order.assigned_rider:
            order.delivery_status = 'DELIVERED'
            order.save()
            
            # Update rider status
            rider = order.assigned_rider
            rider.status = 'Available'
            rider.save()
            
            # Create earnings record
            DeliveryEarning.objects.create(
                rider=rider,
                order=order,
                amount=order.delivery_fee,
                paid=False
            ) 