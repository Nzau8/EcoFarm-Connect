from django import forms
from .models import Comment, Discussion, Post, Product, Cart, Negotiation, Order, Notification
from .models import Seller, Buyer, BodaRider
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    UserProfile, CommunityPost, CommunityGroup,
    Event, LiveStream, Report, Poll
)


# Comment Form (for adding comments)
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Write a comment...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''  # Remove label for cleaner UI

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
        fields = ['name', 'description', 'price', 'stock', 'unit', 'location', 'image', 'delivery_available', 'delivery_fee', 'farm_pickup', 'farm_pickup_instructions', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your product'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'delivery_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'delivery_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'farm_pickup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'farm_pickup_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

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


# class ContactForm(forms.Form):
#     name = forms.CharField(max_length=100, required=True)
#     email = forms.EmailField(required=True)
#     subject = forms.CharField(max_length=200, required=True)
#     message = forms.CharField(widget=forms.Textarea, required=True)

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
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


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'location', 'website']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CommunityPostForm(forms.ModelForm):
    hashtags_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add hashtags (e.g., #farming #organic)'
        })
    )
    
    class Meta:
        model = CommunityPost
        fields = ['content', 'image', 'group']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'What\'s on your mind?'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'group': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = CommunityGroup
        fields = ['name', 'description', 'cover_image', 'is_private']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_time', 'end_time', 'location', 'is_online', 'meeting_link', 'group']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }

class LiveStreamForm(forms.ModelForm):
    class Meta:
        model = LiveStream
        fields = ['title', 'description', 'scheduled_start', 'group']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'scheduled_start': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'reason']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Please explain why you are reporting this content...'
            }),
        }

class PollForm(forms.Form):
    question = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ask a question...'
        })
    )
    options = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Enter one option per line...'
        })
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )




