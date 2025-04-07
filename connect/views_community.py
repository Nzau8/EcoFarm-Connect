from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count, Q, Max
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import (
    UserProfile, CommunityPost, PostReaction, Comment, Hashtag,
    CommunityGroup, Event, LiveStream, Report, Poll, PollOption,
    UserBlock, Badge, Chat, GroupJoinRequest, Notification
)
from .forms import (
    UserProfileForm, CommunityPostForm, CommentForm, GroupForm,
    EventForm, LiveStreamForm, ReportForm, PollForm
)
import json
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import Group

@login_required
def community_home(request):
    search_query = request.GET.get('search')
    category = request.GET.get('category')
    
    # Get posts excluding those from blocked users
    blocked_users = request.user.blocking.values_list('blocked', flat=True)
    posts = CommunityPost.objects.filter(
        group__isnull=True  # Only show public posts
    ).exclude(
        author__in=blocked_users
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'reactions', 'comments', 'hashtags'
    ).order_by('-created_at')
    
    # Apply filters
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(hashtags__name__icontains=search_query)
        ).distinct()
    
    if category:
        posts = posts.filter(categories__contains=[category])
    
    # Get categories from choices
    categories = [choice[1] for choice in CommunityPost.CATEGORY_CHOICES]
    
    # Pagination
    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
    }
    return render(request, 'connect/community_home.html', context)

@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if the logged-in user has blocked this profile
    is_blocked = UserBlock.objects.filter(
        blocker=request.user,
        blocked=user
    ).exists()
    
    if is_blocked:
        return HttpResponseForbidden("You have blocked this user")
    
    posts = CommunityPost.objects.filter(author=user).order_by('-created_at')
    
    context = {
        'profile': profile,
        'posts': posts,
        'is_following': request.user.following.filter(id=user.id).exists(),
        'followers_count': profile.get_followers_count(),
        'following_count': profile.get_following_count(),
    }
    return render(request, 'connect/community/profile.html', context)

@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('connect:profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'connect/community/edit_profile.html', {'form': form})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = CommunityPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # Handle hashtags
            hashtag_text = form.cleaned_data.get('hashtags_text', '')
            if hashtag_text:
                hashtags = [tag.strip('#') for tag in hashtag_text.split() if tag.startswith('#')]
                for tag_name in hashtags:
                    hashtag, created = Hashtag.objects.get_or_create(name=tag_name)
                    if created:
                        hashtag.usage_count = 1
                    else:
                        hashtag.usage_count += 1
                    hashtag.save()
                    post.hashtags.add(hashtag)
            
            messages.success(request, 'Post created successfully!')
            return redirect('connect:community_home')
    else:
        form = CommunityPostForm()
    
    return render(request, 'connect/community/create_post.html', {'form': form})

@login_required
def create_discussion(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        categories = request.POST.getlist('categories')
        tags = request.POST.get('tags', '').split(',')
        
        # Create the post
        post = CommunityPost.objects.create(
            title=title,
            content=content,
            author=request.user,
            categories=categories
        )
        
        # Handle tags
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag, _ = Hashtag.objects.get_or_create(name=tag_name.lower())
                post.hashtags.add(tag)
        
        messages.success(request, 'Discussion created successfully!')
        return JsonResponse({'status': 'success', 'redirect_url': reverse('connect:community_home')})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    comments = Comment.objects.filter(post=post, parent__isnull=True).prefetch_related('replies')
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('connect:post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'connect/community/post_detail.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            group.members.add(request.user)
            group.moderators.add(request.user)
            messages.success(request, 'Group created successfully!')
            return redirect('connect:group_detail', group_id=group.id)
    else:
        form = GroupForm()
    
    return render(request, 'connect/community/create_group.html', {'form': form})

@login_required
def edit_group(request, group_id):
    group = get_object_or_404(CommunityGroup, id=group_id)
    
    # Check if user is authorized to edit the group
    if request.user != group.creator and not request.user in group.moderators.all():
        return HttpResponseForbidden("You don't have permission to edit this group")
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated successfully!')
            return redirect('connect:group_detail', group_id=group.id)
    else:
        form = GroupForm(instance=group)
    
    return render(request, 'connect/community/edit_group.html', {
        'form': form,
        'group': group
    })

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(CommunityGroup, id=group_id)
    posts = CommunityPost.objects.filter(group=group).order_by('-created_at')
    
    is_member = request.user in group.members.all()
    is_moderator = request.user in group.moderators.all()
    
    if group.is_private and not is_member:
        return HttpResponseForbidden("This is a private group")
    
    context = {
        'group': group,
        'posts': posts,
        'is_member': is_member,
        'is_moderator': is_moderator,
        'member_count': group.members.count(),
    }
    return render(request, 'connect/community/group_detail.html', context)

@login_required
def group_list(request):
    groups = CommunityGroup.objects.annotate(
        member_count=Count('members')
    ).order_by('-member_count')
    
    # Filter by search query if provided
    search_query = request.GET.get('q')
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(groups, 12)
    page = request.GET.get('page')
    groups = paginator.get_page(page)
    
    return render(request, 'connect/community/group_list.html', {
        'groups': groups,
        'search_query': search_query
    })

@login_required
def join_group(request, group_id):
    group = get_object_or_404(CommunityGroup, id=group_id)
    
    if request.method == 'POST':
        if request.user in group.members.all():
            group.members.remove(request.user)
            messages.success(request, f'You have left {group.name}')
        else:
            group.members.add(request.user)
            messages.success(request, f'You have joined {group.name}')
        
        return redirect('connect:group_detail', group_id=group.id)
    
    return HttpResponseForbidden("Invalid request method")

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(CommunityGroup, id=group_id)
    
    if request.method == 'POST':
        if request.user in group.members.all():
            # Don't allow the creator to leave if they're the only moderator
            if group.creator == request.user and group.moderators.count() == 1:
                messages.error(request, "As the group creator, you cannot leave until you assign another moderator.")
                return redirect('connect:group_detail', group_id=group.id)
            
            group.members.remove(request.user)
            group.moderators.remove(request.user)
            messages.success(request, f'You have left {group.name}')
        
        return redirect('connect:groups')
    
    return HttpResponseForbidden("Invalid request method")

# AJAX views for real-time interactions
@login_required
def toggle_reaction(request, post_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        post = get_object_or_404(CommunityPost, id=post_id)
        reaction, created = PostReaction.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            if reaction.reaction_type == reaction_type:
                reaction.delete()
                action = 'removed'
            else:
                reaction.reaction_type = reaction_type
                reaction.save()
                action = 'changed'
        else:
            action = 'added'
        
        # Get updated reaction counts for all types
        reaction_counts = {
            reaction_type: post.get_reaction_count(reaction_type)
            for reaction_type, _ in CommunityPost.REACTION_CHOICES
        }
        
        return JsonResponse({
            'status': 'success',
            'action': action,
            'reaction_counts': reaction_counts
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def toggle_follow(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        user_to_follow = User.objects.get(id=user_id)
        profile = request.user.profile
        
        if user_to_follow == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot follow yourself'})
        
        if profile.followers.filter(id=user_to_follow.id).exists():
            profile.followers.remove(user_to_follow)
            is_following = False
        else:
            profile.followers.add(user_to_follow)
            is_following = True
        
        return JsonResponse({
            'success': True,
            'is_following': is_following,
            'followers_count': user_to_follow.profile.get_followers_count()
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})

@login_required
def poll_list(request):
    # Get active polls (not ended)
    active_polls = Poll.objects.filter(
        end_date__gt=timezone.now()
    ).select_related('post').order_by('-created_at')
    
    # Get ended polls
    ended_polls = Poll.objects.filter(
        end_date__lte=timezone.now()
    ).select_related('post').order_by('-end_date')
    
    context = {
        'active_polls': active_polls,
        'ended_polls': ended_polls,
    }
    return render(request, 'connect/community/poll_list.html', context)

@login_required
def create_poll(request):
    if request.method == 'POST':
        form = PollForm(request.POST)
        if form.is_valid():
            # Create the post first
            post = CommunityPost.objects.create(
                author=request.user,
                content=form.cleaned_data['question'],
                is_poll=True
            )
            
            # Create the poll
            poll = Poll.objects.create(
                post=post,
                question=form.cleaned_data['question'],
                end_date=form.cleaned_data['end_date']
            )
            
            # Create poll options
            options = form.cleaned_data['options'].split('\n')
            for option_text in options:
                if option_text.strip():
                    PollOption.objects.create(
                        poll=poll,
                        text=option_text.strip()
                    )
            
            messages.success(request, 'Poll created successfully!')
            return redirect('connect:post_detail', post_id=post.id)
    else:
        form = PollForm()
    
    return render(request, 'connect/community/create_poll.html', {'form': form})

@login_required
def vote_poll(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        option_id = data.get('option_id')
        option = get_object_or_404(PollOption, id=option_id)
        
        # Check if poll has ended
        if option.poll.end_date < timezone.now():
            return JsonResponse({'error': 'This poll has ended'}, status=400)
        
        # Remove any existing votes by this user on this poll
        option.poll.options.filter(votes=request.user).update(votes=None)
        
        # Add the new vote
        option.votes.add(request.user)
        
        return JsonResponse({
            'success': True,
            'results': {
                opt.id: opt.get_vote_count()
                for opt in option.poll.options.all()
            }
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def report_content(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        report = Report.objects.create(
            reporter=request.user,
            reported_user_id=data.get('reported_user'),
            report_type=data['report_type'],
            reason=data['reason']
        )
        return JsonResponse({'success': True})
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid request data'})

@login_required
def toggle_block_user(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        user_to_block = User.objects.get(id=user_id)
        
        if user_to_block == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot block yourself'})
        
        block, created = UserBlock.objects.get_or_create(
            blocker=request.user,
            blocked=user_to_block
        )
        
        if not created:
            block.delete()
        
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})

# Event and Live Streaming views
@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            
            # Create a post for the event
            post = CommunityPost.objects.create(
                author=request.user,
                content=f"New Event: {event.title}\n\n{event.description}",
                is_event=True
            )
            
            messages.success(request, 'Event created successfully!')
            return redirect('connect:event_detail', event_id=event.id)
    else:
        form = EventForm()
    
    return render(request, 'connect/community/create_event.html', {'form': form})

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_attending = request.user in event.attendees.all()
    
    if request.method == 'POST':
        if 'attend' in request.POST:
            if is_attending:
                event.attendees.remove(request.user)
                messages.success(request, 'You are no longer attending this event.')
            else:
                event.attendees.add(request.user)
                messages.success(request, 'You are now attending this event!')
            return redirect('connect:event_detail', event_id=event.id)
    
    context = {
        'event': event,
        'is_attending': is_attending,
        'attendees_count': event.attendees.count(),
    }
    return render(request, 'connect/community/event_detail.html', context)

@login_required
def event_list(request):
    # Get current and upcoming events
    current_time = timezone.now()
    events = Event.objects.filter(
        end_time__gte=current_time
    ).order_by('start_time')
    
    # Filter by search query if provided
    search_query = request.GET.get('q')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(events, 12)
    page = request.GET.get('page')
    events = paginator.get_page(page)
    
    return render(request, 'connect/community/event_list.html', {
        'events': events,
        'search_query': search_query
    })

@login_required
def toggle_attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        if request.user in event.attendees.all():
            event.attendees.remove(request.user)
            messages.success(request, f'You are no longer attending {event.title}')
        else:
            event.attendees.add(request.user)
            messages.success(request, f'You are now attending {event.title}')
        
        return redirect('connect:event_detail', event_id=event.id)
    
    return HttpResponseForbidden("Invalid request method")

@login_required
def create_live_stream(request):
    if request.method == 'POST':
        form = LiveStreamForm(request.POST)
        if form.is_valid():
            stream = form.save(commit=False)
            stream.streamer = request.user
            stream.save()
            
            # Create a post for the live stream
            post = CommunityPost.objects.create(
                author=request.user,
                content=f"🔴 Live Stream: {stream.title}\n\n{stream.description}",
                is_live_stream=True
            )
            
            messages.success(request, 'Live stream created successfully!')
            return redirect('connect:stream_detail', stream_id=stream.id)
    else:
        form = LiveStreamForm()
    
    return render(request, 'connect/community/create_stream.html', {'form': form})

@login_required
def stream_detail(request, stream_id):
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    if request.method == 'POST':
        if 'start_stream' in request.POST and request.user == stream.streamer:
            stream.is_live = True
            stream.actual_start = timezone.now()
            stream.save()
        elif 'end_stream' in request.POST and request.user == stream.streamer:
            stream.is_live = False
            stream.actual_end = timezone.now()
            stream.save()
    
    context = {
        'stream': stream,
        'is_streamer': request.user == stream.streamer,
        'viewer_count': stream.viewers.count(),
    }
    return render(request, 'connect/community/stream_detail.html', context)

@login_required
def stream_list(request):
    # Get current and scheduled streams
    current_time = timezone.now()
    live_streams = LiveStream.objects.filter(
        Q(is_live=True) |
        Q(scheduled_start__gte=current_time)
    ).order_by('scheduled_start')
    
    # Filter by search query if provided
    search_query = request.GET.get('q')
    if search_query:
        live_streams = live_streams.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(live_streams, 12)
    page = request.GET.get('page')
    live_streams = paginator.get_page(page)
    
    return render(request, 'connect/community/stream_list.html', {
        'live_streams': live_streams,
        'search_query': search_query
    })

@login_required
def hashtag_view(request, name):
    hashtag = get_object_or_404(Hashtag, name=name)
    posts = CommunityPost.objects.filter(
        hashtags=hashtag
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'connect/community/hashtag.html', {
        'hashtag': hashtag,
        'posts': posts
    })

@login_required
def category_view(request, name):
    # Get posts for the specific category excluding blocked users
    blocked_users = request.user.blocking.values_list('blocked', flat=True)
    posts = CommunityPost.objects.filter(
        categories__contains=[name]
    ).exclude(
        author__in=blocked_users
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'reactions', 'comments', 'hashtags'
    ).order_by('-created_at')

    # Get categories from choices for the sidebar
    categories = [choice[1] for choice in CommunityPost.CATEGORY_CHOICES]
    
    # Pagination
    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'category_name': name,
        'posts': posts,
        'categories': categories,
        'post_count': posts.paginator.count,
    }
    return render(request, 'connect/community/category.html', context)

@login_required
def chat_list(request):
    # Get all chats where the user is a participant
    chats = Chat.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__timestamp')
    ).order_by('-last_message_time')
    
    return render(request, 'connect/community/chat_list.html', {
        'chats': chats
    })

@login_required
def start_chat(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        other_user = User.objects.get(id=data['user_id'])
        
        # Check if chat already exists
        existing_chat = Chat.objects.filter(participants=request.user).filter(participants=other_user).first()
        
        if existing_chat:
            chat = existing_chat
        else:
            chat = Chat.objects.create()
            chat.participants.add(request.user, other_user)
        
        return JsonResponse({
            'success': True,
            'chat_url': reverse('connect:chat_detail', args=[chat.id])
        })
    except (User.DoesNotExist, KeyError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Ensure user is a participant
    if request.user not in chat.participants.all():
        return HttpResponseForbidden("You are not a participant in this chat")
    
    messages = chat.messages.order_by('-timestamp')[:50]
    
    return render(request, 'connect/community/chat_detail.html', {
        'chat': chat,
        'messages': messages
    })

@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        post = get_object_or_404(CommunityPost, id=post_id)
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=data.get('content')
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': {
                    'username': comment.author.username,
                    'profile_picture': comment.author.profile.profile_picture.url if comment.author.profile.profile_picture else None,
                    'full_name': comment.author.get_full_name() or comment.author.username
                },
                'created_at': comment.created_at.strftime('%b %d, %Y %H:%M')
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@require_POST
def update_profile_picture(request):
    """Handle profile picture updates via AJAX."""
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'error': 'No image file provided'}, status=400)
    
    try:
        profile = request.user.profile
        # Delete old profile picture if it exists
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)
        
        # Save new profile picture
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        
        return JsonResponse({
            'success': True,
            'url': profile.profile_picture.url
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    
    # Check if user is authorized to edit the post
    if request.user != post.author:
        return HttpResponseForbidden("You don't have permission to edit this post")
    
    if request.method == 'POST':
        form = CommunityPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.updated_at = timezone.now()
            post.save()
            
            # Handle hashtags
            hashtag_text = form.cleaned_data.get('hashtags_text', '')
            if hashtag_text:
                # Clear existing hashtags
                post.hashtags.clear()
                # Add new hashtags
                hashtags = [tag.strip('#') for tag in hashtag_text.split() if tag.startswith('#')]
                for tag_name in hashtags:
                    hashtag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
                    if created:
                        hashtag.usage_count = 1
                    else:
                        hashtag.usage_count += 1
                    hashtag.save()
                    post.hashtags.add(hashtag)
            
            messages.success(request, 'Post updated successfully!')
            return redirect('connect:post_detail', post_id=post.id)
    else:
        # Pre-fill hashtags
        initial_hashtags = ' '.join([f'#{tag.name}' for tag in post.hashtags.all()])
        form = CommunityPostForm(instance=post, initial={'hashtags_text': initial_hashtags})
    
    return render(request, 'connect/community/edit_post.html', {
        'form': form,
        'post': post
    })

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    
    # Check if user is authorized to delete the post
    if request.user != post.author and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to delete this post")
    
    if request.method == 'POST':
        # Store the group id if the post belongs to a group
        group_id = post.group.id if post.group else None
        
        # Delete associated media file if it exists
        if post.media:
            post.media.delete(save=False)
        
        # Delete the post
        post.delete()
        
        messages.success(request, 'Post deleted successfully!')
        
        # Redirect to appropriate page
        if group_id:
            return redirect('connect:group_detail', group_id=group_id)
        return redirect('connect:community_home')
    
    return render(request, 'connect/community/delete_post.html', {
        'post': post
    })

@login_required
def request_join_group(request, group_id):
    """Handle join requests for private groups"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        group = CommunityGroup.objects.get(id=group_id)
        
        # Check if the group is private
        if not group.is_private:
            return JsonResponse({'error': 'This group is not private'}, status=400)
            
        # Check if user is already a member
        if request.user in group.members.all():
            return JsonResponse({'error': 'You are already a member of this group'}, status=400)
            
        # Check if user already has a pending request
        if GroupJoinRequest.objects.filter(user=request.user, group=group, status='pending').exists():
            return JsonResponse({'error': 'You already have a pending request to join this group'}, status=400)
            
        # Create the join request
        join_request = GroupJoinRequest.objects.create(
            user=request.user,
            group=group,
            status='pending'
        )
        
        # Using our custom Notification model
        Notification.objects.create(
            user=group.creator,
            message=f"{request.user.get_full_name()} requested to join {group.name}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Join request sent successfully'
        })
        
    except CommunityGroup.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    