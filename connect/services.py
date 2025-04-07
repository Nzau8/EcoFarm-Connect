from django.db.models import Q
from .models import BodaRider, Order, DeliveryEarning
from datetime import datetime
from django.db import connection
from django.utils import timezone

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

class ReviewService:
    @staticmethod
    def create_product_review(product_id, buyer_id, order_id, rating, comment):
        with connection.cursor() as cursor:
            # Check if buyer has purchased the product
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM connect_order o
                    JOIN connect_orderitem oi ON o.id = oi.order_id
                    WHERE o.buyer_id = %s 
                    AND oi.product_id = %s
                    AND o.id = %s
                    AND o.payment_status = 'COMPLETED'
                )
            """, [buyer_id, product_id, order_id])
            
            has_purchased = cursor.fetchone()[0]
            
            if not has_purchased:
                raise ValueError("Can only review purchased products")
            
            # Check if review already exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM connect_productreview
                    WHERE product_id = %s 
                    AND buyer_id = %s
                    AND order_id = %s
                )
            """, [product_id, buyer_id, order_id])
            
            review_exists = cursor.fetchone()[0]
            
            if review_exists:
                raise ValueError("Review already exists for this order")
            
            # Insert review
            cursor.execute("""
                INSERT INTO connect_productreview 
                (product_id, buyer_id, order_id, rating, comment, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [product_id, buyer_id, order_id, rating, comment, timezone.now()])
            
            # Update product average rating
            cursor.execute("""
                UPDATE connect_product 
                SET avg_rating = (
                    SELECT AVG(rating) 
                    FROM connect_productreview 
                    WHERE product_id = %s
                )
                WHERE id = %s
            """, [product_id, product_id])

    @staticmethod
    def create_seller_review(seller_id, buyer_id, order_id, rating, comment):
        with connection.cursor() as cursor:
            # Check if buyer has purchased from seller
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM connect_order o
                    WHERE o.buyer_id = %s 
                    AND o.seller_id = %s
                    AND o.id = %s
                    AND o.payment_status = 'COMPLETED'
                )
            """, [buyer_id, seller_id, order_id])
            
            has_purchased = cursor.fetchone()[0]
            
            if not has_purchased:
                raise ValueError("Can only review sellers you've purchased from")
            
            # Check if review already exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM connect_sellerreview
                    WHERE seller_id = %s 
                    AND buyer_id = %s
                    AND order_id = %s
                )
            """, [seller_id, buyer_id, order_id])
            
            review_exists = cursor.fetchone()[0]
            
            if review_exists:
                raise ValueError("Review already exists for this order")
            
            # Insert review
            cursor.execute("""
                INSERT INTO connect_sellerreview 
                (seller_id, buyer_id, order_id, rating, comment, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [seller_id, buyer_id, order_id, rating, comment, timezone.now()])
            
            # Update seller average rating
            cursor.execute("""
                UPDATE connect_seller 
                SET avg_rating = (
                    SELECT AVG(rating) 
                    FROM connect_sellerreview 
                    WHERE seller_id = %s
                )
                WHERE id = %s
            """, [seller_id, seller_id])

    @staticmethod
    def get_product_reviews(product_id, cursor_id=None, limit=10):
        with connection.cursor() as cursor:
            if cursor_id:
                cursor.execute("""
                    SELECT r.id, r.rating, r.comment, r.created_at,
                           u.username, u.first_name, u.last_name
                    FROM connect_productreview r
                    JOIN auth_user u ON r.buyer_id = u.id
                    WHERE r.product_id = %s
                    AND r.id < %s
                    ORDER BY r.id DESC
                    LIMIT %s
                """, [product_id, cursor_id, limit])
            else:
                cursor.execute("""
                    SELECT r.id, r.rating, r.comment, r.created_at,
                           u.username, u.first_name, u.last_name
                    FROM connect_productreview r
                    JOIN auth_user u ON r.buyer_id = u.id
                    WHERE r.product_id = %s
                    ORDER BY r.id DESC
                    LIMIT %s
                """, [product_id, limit])
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_seller_reviews(seller_id, cursor_id=None, limit=10):
        with connection.cursor() as cursor:
            if cursor_id:
                cursor.execute("""
                    SELECT r.id, r.rating, r.comment, r.created_at,
                           u.username, u.first_name, u.last_name
                    FROM connect_sellerreview r
                    JOIN auth_user u ON r.buyer_id = u.id
                    WHERE r.seller_id = %s
                    AND r.id < %s
                    ORDER BY r.id DESC
                    LIMIT %s
                """, [seller_id, cursor_id, limit])
            else:
                cursor.execute("""
                    SELECT r.id, r.rating, r.comment, r.created_at,
                           u.username, u.first_name, u.last_name
                    FROM connect_sellerreview r
                    JOIN auth_user u ON r.buyer_id = u.id
                    WHERE r.seller_id = %s
                    ORDER BY r.id DESC
                    LIMIT %s
                """, [seller_id, limit])
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()] 