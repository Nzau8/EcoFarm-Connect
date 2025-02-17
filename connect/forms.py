from django import forms
from .models import Comment, Discussion, Post, Product, Cart, Negotiation, Order, Notification
from .models import Seller, Buyer, BodaRider
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# Comment Form (for adding comments)
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

# Form for creating a discussion
class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter discussion title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your discussion topic'
            })
        }

    def __init__(self, *args, **kwargs):
        super(DiscussionForm, self).__init__(*args, **kwargs)
        # Additional initialization if necessary

# Form for adding a post to a discussion
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']

# Form for searching discussions
class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=False)
    tag = forms.CharField(max_length=50, required=False)

# Product Form (for sellers adding and editing products)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock']

# Cart Form (for adding products to the cart)
class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['product', 'quantity']

# Negotiation Form (for buyers negotiating with sellers)
class NegotiationForm(forms.ModelForm):
    class Meta:
        model = Negotiation
        fields = ['status']

# Notification Form (for creating notifications for users)
class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['message']


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

# Seller Profile Form (for sellers to update their profiles)
class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ['company_name', 'location', 'phone_number', 'email']

# Buyer Profile Form (for buyers to update their profiles)
class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['address', 'phone_number', 'email']

# Boda Rider Profile Form (for boda riders to update their profiles)
class BodaRiderProfileForm(forms.ModelForm):
    class Meta:
        model = BodaRider
        fields = ['bike_model', 'license_number', 'location', 'phone_number']


class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('bodarider', 'Boda Rider'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    phone_number = forms.CharField(max_length=15)
    
    # Seller-specific fields
    company_name = forms.CharField(max_length=255, required=False)
    location = forms.CharField(max_length=255, required=False)
    
    # Boda Rider-specific fields
    bike_model = forms.CharField(max_length=100, required=False)
    license_number = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Seller
        fields = ['company_name', 'location', 'phone_number', 'email']


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = Buyer
        fields = ['address', 'phone_number', 'email']


class BodaRiderProfileForm(forms.ModelForm):
    class Meta:
        model = BodaRider
        fields = ['bike_model', 'license_number', 'location', 'phone_number']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }




