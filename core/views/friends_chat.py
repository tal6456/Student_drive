"""
Friends and private chat views
==============================

This file groups the peer-to-peer interactions on the site.
It manages friendship flows, public profiles, user search,
and private chat rooms with optional file attachments.
"""


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth import get_user_model

# Import only the models required by this module
from core.models import Friendship, Notification, Post, Document, ChatRoom, ChatMessage

User = get_user_model()


# ==========================================
# 1. Public profile and friend requests
# ==========================================

@login_required
def public_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile

    # Delete a notification if the user opened the page through it
    notification_id = request.GET.get('delete')
    if notification_id:
        Notification.objects.filter(id=notification_id, user=request.user).delete()

    if target_profile.profile_visibility == 'private' and request.user != target_user:
        messages.warning(request, "פרופיל זה הוא פרטי.")
        return redirect('home')

    user_posts = Post.objects.filter(user=target_user).order_by('-created_at')
    user_documents = Document.objects.filter(uploaded_by=target_user).order_by('-upload_date')

    friendship_status = 'none'
    friend_request_id = None

    if request.user != target_user:
        relation = Friendship.objects.filter(
            models.Q(user_from=request.user, user_to=target_user) |
            models.Q(user_from=target_user, user_to=request.user)
        ).first()

        if relation:
            if relation.status == 'accepted':
                friendship_status = 'friends'
                friend_request_id = relation.id

                Notification.objects.filter(
                    user=request.user,
                    sender=target_user,
                    notification_type='friend_request'
                ).delete()

            elif relation.status == 'pending':
                if relation.user_from == request.user:
                    friendship_status = 'request_sent'
                    friend_request_id = relation.id
                else:
                    friendship_status = 'request_received'
                    friend_request_id = relation.id

    context = {
        'target_user': target_user,
        'target_profile': target_profile,
        'posts': user_posts,
        'documents': user_documents,
        'friendship_status': friendship_status,
        'friend_request_id': friend_request_id,
    }
    return render(request, 'core/public_profile.html', context)


@login_required
def send_friend_request(request, username):
    user_to = get_object_or_404(User, username=username)
    if request.user == user_to:
        messages.warning(request, "אי אפשר לשלוח בקשת חברות לעצמך.")
        return redirect('public_profile', username=username)

    existing_relation = Friendship.objects.filter(
        models.Q(user_from=request.user, user_to=user_to) |
        models.Q(user_from=user_to, user_to=request.user)
    ).first()

    if not existing_relation:
        Friendship.objects.create(user_from=request.user, user_to=user_to, status='pending')

        Notification.objects.get_or_create(
            user=user_to,
            sender=request.user,
            notification_type='friend_request',
            title="בקשת חברות חדשה",
            defaults={
                'message': f"{request.user.username} שלח לך בקשת חברות!",
                'link': reverse('public_profile', kwargs={'username': request.user.username})
            }
        )
        messages.success(request, f"בקשת חברות נשלחה אל {username}!")

    return redirect('public_profile', username=username)


@login_required
def accept_friend_request(request, request_id):
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friend_req.status = 'accepted'
    friend_req.save()

    Notification.objects.filter(
        user=request.user,
        sender=friend_req.user_from,
        notification_type='friend_request'
    ).delete()

    Notification.objects.create(
        user=friend_req.user_from,
        sender=request.user,
        notification_type='system',
        title="בקשת החברות אושרה!",
        message=f"{request.user.username} אישר את בקשת החברות שלך. עכשיו אתם חברים!",
        link=reverse('public_profile', kwargs={'username': request.user.username})
    )

    messages.success(request, f"איזה כיף! אתה ו-{friend_req.user_from.username} עכשיו חברים.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def reject_friend_request(request, request_id):
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')

    Notification.objects.filter(
        user=request.user,
        sender=friend_req.user_from,
        notification_type='friend_request'
    ).delete()

    friend_req.delete()
    messages.info(request, "בקשת החברות נמחקה.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ==========================================
# 2. Friends list management
# ==========================================

@login_required
def my_friends(request):
    friends = request.user.profile.get_accepted_friends
    return render(request, 'core/friends_list.html', {'friends': friends})


@login_required
def remove_friend(request, friend_username):
    friend_user = get_object_or_404(User, username=friend_username)
    Friendship.objects.filter(
        (models.Q(user_from=request.user, user_to=friend_user) |
         models.Q(user_from=friend_user, user_to=request.user)),
        status='accepted'
    ).delete()
    messages.success(request, f"הסרת את {friend_username} מרשימת החברים שלך.")
    return redirect('my_friends')


@login_required
def search_users(request):
    query = request.GET.get('q', '').strip()
    pending_requests = Friendship.objects.filter(user_to=request.user, status='pending')

    users = []
    if query:
        users = User.objects.filter(
            Q(username__iexact=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')[:20]
    else:
        friendships = Friendship.objects.filter(
            (Q(user_from=request.user) | Q(user_to=request.user)),
            status='accepted'
        )
        users = [f.user_to if f.user_from == request.user else f.user_from for f in friendships]

    context = {
        'query': query,
        'friends': users,
        'pending_requests': pending_requests,
    }
    return render(request, 'core/friends_list.html', context)


# ==========================================
# 3. Private chat
# ==========================================

@login_required
def get_or_create_chat(request, username):
    target_user = get_object_or_404(User, username=username)

    room = ChatRoom.objects.filter(participants=request.user).filter(participants=target_user).first()

    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(request.user, target_user)

    return redirect('chat_room', room_id=room.id)


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    all_chat_messages = room.messages.all().order_by('timestamp')
    my_documents = Document.objects.filter(uploaded_by=request.user)

    if request.method == 'POST':
        content = request.POST.get('content')
        drive_file_id = request.POST.get('drive_file_id')
        local_file = request.FILES.get('local_file')

        if content or drive_file_id or local_file:
            msg = ChatMessage.objects.create(
                room=room,
                sender=request.user,
                content=content
            )

            if drive_file_id:
                try:
                    msg.attached_file = Document.objects.get(id=drive_file_id, uploaded_by=request.user)
                except Document.DoesNotExist:
                    pass

            elif local_file:
                # Files uploaded in chat are intentionally stored without a course
                new_doc = Document.objects.create(
                    uploaded_by=request.user,
                    title=local_file.name,
                    file=local_file,
                    course=None
                )
                msg.attached_file = new_doc

            msg.save()
            return redirect('chat_room', room_id=room.id)

    return render(request, 'core/chat_room.html', {
        'room': room,
        'chat_messages': all_chat_messages,
        'my_documents': my_documents
    })
