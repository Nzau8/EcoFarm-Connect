// Community Interactions

// Handle comment submission
function submitComment(event, postId, parentId = null) {
    event.preventDefault();
    const form = event.target;
    const textarea = form.querySelector('textarea[name="content"]');
    const content = textarea.value.trim();
    
    if (!content) return;
    
    fetch(`/community/post/${postId}/comment/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 
            content: content,
            parent_id: parentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Add new comment to the list
            const commentHtml = createCommentHtml(data.comment);
            
            if (parentId) {
                // Add reply to the replies list
                const repliesList = document.getElementById(`replies-${parentId}`);
                repliesList.insertAdjacentHTML('beforeend', commentHtml);
                
                // Hide reply form
                const replyForm = document.getElementById(`reply-form-${parentId}`);
                replyForm.classList.add('d-none');
                replyForm.querySelector('textarea').value = '';
            } else {
                // Add comment to the main comments list
                const commentsList = document.getElementById(`comments-${postId}`);
                commentsList.insertAdjacentHTML('afterbegin', commentHtml);
            }
            
            // Update comment count
            updateCommentCount(postId, 1);
            
            // Clear the textarea
            textarea.value = '';
            textarea.style.height = 'auto';
        }
    })
    .catch(error => console.error('Error:', error));
}

// Create HTML for a new comment
function createCommentHtml(comment) {
    return `
        <div class="comment-thread" id="comment-${comment.id}">
            <div class="comment-item">
                <img src="${comment.author.profile_picture || '/static/connect/images/default_profile.png'}" 
                     alt="${comment.author.username}" 
                     class="comment-avatar">
                <div class="comment-content">
                    <div class="comment-header">
                        <a href="/community/profile/${comment.author.username}/" 
                           class="comment-author">
                            ${comment.author.full_name || comment.author.username}
                        </a>
                        <span class="comment-time">just now</span>
                    </div>
                    <p class="comment-text">${comment.content}</p>
                    <div class="comment-actions">
                        <button class="btn btn-link btn-sm" onclick="likeComment(${comment.id})">
                            <i class="bi bi-hand-thumbs-up"></i> Like
                        </button>
                        <button class="btn btn-link btn-sm" onclick="showReplyForm(${comment.id})">
                            Reply
                        </button>
                    </div>
                    <div class="reply-form d-none" id="reply-form-${comment.id}">
                        <form onsubmit="submitComment(event, ${comment.post_id}, ${comment.id})" class="d-flex mt-2">
                            <img src="${currentUserProfilePic}" 
                                 alt="${currentUsername}" 
                                 class="comment-avatar comment-avatar-sm">
                            <div class="flex-grow-1">
                                <div class="d-flex gap-2 align-items-start">
                                    <textarea class="form-control" 
                                              name="content"
                                              rows="1" 
                                              placeholder="Write a reply..."
                                              oninput="autoResize(this)"></textarea>
                                    <button type="submit" class="btn btn-primary px-3 py-2">
                                        <i class="bi bi-send fs-5"></i>
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="replies-list" id="replies-${comment.id}"></div>
                </div>
            </div>
        </div>
    `;
}

// Handle reactions
function toggleReaction(postId, reactionType) {
    fetch(`/community/post/${postId}/react/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            reaction_type: reactionType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update reaction counts and UI
            updateReactionUI(postId, data.reactions);
            
            // Update reaction button state
            const reactionButton = document.querySelector(`#post-${postId} .reaction-${reactionType.toLowerCase()}`);
            if (data.action === 'added') {
                reactionButton.classList.add('active');
            } else {
                reactionButton.classList.remove('active');
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

// Update reaction UI
function updateReactionUI(postId, reactions) {
    const reactionsContainer = document.querySelector(`#post-${postId} .reactions-summary`);
    const totalCount = Object.values(reactions).reduce((a, b) => a + b, 0);
    
    // Update total count
    reactionsContainer.querySelector('.reactions-count').textContent = `${totalCount} reactions`;
    
    // Update individual reaction counts
    Object.entries(reactions).forEach(([type, count]) => {
        const reactionElement = reactionsContainer.querySelector(`.reaction-${type.toLowerCase()}`);
        if (reactionElement) {
            reactionElement.setAttribute('title', `${count} ${type}`);
        }
    });
}

// Function to toggle follow/unfollow
function toggleFollow(userId) {
    fetch(`/community/user/${userId}/follow/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const button = document.querySelector('.profile-actions button');
            const icon = button.querySelector('i');
            const text = button.querySelector('.follow-text');
            
            if (data.is_following) {
                button.classList.remove('btn-success');
                button.classList.add('btn-outline-success');
                icon.classList.remove('bi-person-plus');
                icon.classList.add('bi-person-dash');
                text.textContent = 'Unfollow';
            } else {
                button.classList.remove('btn-outline-success');
                button.classList.add('btn-success');
                icon.classList.remove('bi-person-dash');
                icon.classList.add('bi-person-plus');
                text.textContent = 'Follow';
            }
            
            // Update followers count
            const followersCount = document.querySelector('.stat-value');
            followersCount.textContent = data.followers_count;
        }
    });
}

// Function to start a chat with a user
function startChat(userId) {
    fetch('/community/chat/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.chat_url;
        }
    });
}

// Function to report a user
function reportUser(userId) {
    const reason = prompt('Please provide a reason for reporting this user:');
    if (reason) {
        fetch('/community/report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                reported_user: userId,
                report_type: 'USER',
                reason: reason
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Thank you for your report. We will review it shortly.');
            }
        });
    }
}

// Function to block a user
function blockUser(userId) {
    if (confirm('Are you sure you want to block this user? You won\'t see their content anymore.')) {
        fetch(`/community/user/${userId}/block/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        });
    }
}

// Helper functions
function showReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    replyForm.classList.toggle('d-none');
    if (!replyForm.classList.contains('d-none')) {
        replyForm.querySelector('textarea').focus();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function updateCommentCount(postId, increment) {
    const commentCount = document.querySelector(`#post-${postId} .comments-count`);
    const currentCount = parseInt(commentCount.textContent.split(' ')[0]);
    const newCount = currentCount + increment;
    commentCount.innerHTML = `<i class="bi bi-chat-dots"></i> ${newCount} comments`;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function joinGroup(groupId) {
    fetch(`/community/group/${groupId}/join/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to reflect joined status
            const joinBtn = document.querySelector(`[data-group-id="${groupId}"]`);
            if (joinBtn) {
                joinBtn.textContent = 'Leave Group';
                joinBtn.onclick = () => leaveGroup(groupId);
                joinBtn.classList.replace('btn-primary', 'btn-outline-primary');
            }
            // Update member count if it exists
            const memberCount = document.querySelector('.member-count');
            if (memberCount) {
                const currentCount = parseInt(memberCount.textContent);
                memberCount.textContent = currentCount + 1;
            }
            // Show success message
            alert('Successfully joined the group!');
        } else {
            alert(data.message || 'Failed to join group');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while trying to join the group');
    });
}

function leaveGroup(groupId) {
    if (!confirm('Are you sure you want to leave this group?')) {
        return;
    }

    fetch(`/community/group/${groupId}/leave/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to reflect left status
            const leaveBtn = document.querySelector(`[data-group-id="${groupId}"]`);
            if (leaveBtn) {
                leaveBtn.textContent = 'Join Group';
                leaveBtn.onclick = () => joinGroup(groupId);
                leaveBtn.classList.replace('btn-outline-primary', 'btn-primary');
            }
            // Update member count if it exists
            const memberCount = document.querySelector('.member-count');
            if (memberCount) {
                const currentCount = parseInt(memberCount.textContent);
                memberCount.textContent = currentCount - 1;
            }
            // Show success message
            alert('Successfully left the group');
        } else {
            alert(data.message || 'Failed to leave group');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while trying to leave the group');
    });
}

function requestJoin() {
    const groupId = document.querySelector('[data-group-id]').dataset.groupId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(`/community/group/${groupId}/request-join/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the button to show pending status
            const button = document.querySelector('.btn-primary[onclick="requestJoin()"]');
            button.textContent = 'Request Pending';
            button.disabled = true;
            button.classList.remove('btn-primary');
            button.classList.add('btn-secondary');
            
            // Show success message
            showAlert('success', 'Join request sent successfully');
        } else {
            showAlert('error', data.error || 'Failed to send join request');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('error', 'An error occurred while sending the join request');
    });
} 