from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import CommunityPost, PostReaction, Comment
import json

@login_required
@require_POST
def react_to_post(request, post_id):
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        post = CommunityPost.objects.get(id=post_id)
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
        
        return JsonResponse({
            'status': 'success',
            'action': action,
            'reactions': post.get_reaction_counts()
        })
    except CommunityPost.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def add_comment(request, post_id):
    try:
        data = json.loads(request.body)
        content = data.get('content')
        parent_id = data.get('parent_id')
        
        post = CommunityPost.objects.get(id=post_id)
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent_id=parent_id
        )
        
        return JsonResponse({
            'status': 'success',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': {
                    'username': comment.author.username,
                    'profile_picture': comment.author.profile.profile_picture.url if comment.author.profile.profile_picture else None,
                    'full_name': comment.author.get_full_name() or comment.author.username
                },
                'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
                'likes_count': 0,
                'parent_id': comment.parent_id
            }
        })
    except CommunityPost.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)