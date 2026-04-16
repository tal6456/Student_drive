
"""
Community and social-feed views.

This module was split out to keep the project's social features together.
It handles the main community feed, multiple post types, AJAX likes/comments,
community discovery, and queryset optimization to avoid N+1 issues.
"""



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, Prefetch

# Import only the community-related models
from core.models import Community, Post, MarketplacePost, VideoPost, Comment

@login_required
def community_feed(request):
    profile = request.user.profile
    if not profile.university:
        messages.info(request, "כדי לראות קהילות מותאמות אישית, מומלץ לבחור מוסד לימודים בפרופיל.")

    my_communities = request.user.joined_communities.all()

    community_id = request.GET.get('community')
    if community_id:
        current_community = get_object_or_404(Community, id=community_id)
    else:
        # Auto-create a sensible default community when needed
        if profile.university:
            current_community, created = Community.objects.get_or_create(
                university=profile.university,
                community_type='university',
                defaults={
                    'name': f'קהילת {profile.university.name}',
                    'description': 'הקהילה הרשמית לסטודנטים במוסד זה.'
                }
            )
        else:
            current_community, created = Community.objects.get_or_create(
                community_type='global',
                defaults={
                    'name': 'הקהילה הגלובלית',
                    'description': 'קהילת כלל הסטודנטים בישראל.'
                }
            )

        # Ensure the current user is a member of the active community
        if current_community not in my_communities:
            current_community.members.add(request.user)

    # --- Critical queryset path to keep indentation correct and avoid N+1 queries ---
    if current_community:
        posts = Post.objects.filter(community=current_community).select_related(
            'user', 'user__profile', 'university', 'community',
            'marketplacepost', 'videopost'  # Avoid extra subtype checks in the template
        ).prefetch_related(
            'likes',
            # Pull comments together with their authors and profiles
            Prefetch('comments', queryset=Comment.objects.select_related('user', 'user__profile'))
        )
    else:
        posts = Post.objects.none()

    # Optional filtering by post subtype
    post_filter = request.GET.get('type')
    if post_filter == 'market':
        posts = posts.filter(marketplacepost__isnull=False)

    posts = posts.order_by('-created_at')

    if request.method == 'POST':
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')

        target_community_id = request.POST.get('target_community')
        target_community = get_object_or_404(Community, id=target_community_id) if target_community_id else current_community

        if not target_community:
            messages.error(request, "עליך להיות חבר בקהילה כדי לפרסם פוסט.")
            return redirect('community_feed')

        if content:
            if post_type == 'market':
                MarketplacePost.objects.create(
                    user=request.user, content=content, community=target_community,
                    university=profile.university, category=request.POST.get('category'),
                    price=request.POST.get('price') or None
                )
            elif post_type == 'video':
                VideoPost.objects.create(
                    user=request.user,
                    content=content,
                    community=target_community,
                    university=profile.university,
                    youtube_url=request.POST.get('youtube_url')
                )
            else:
                Post.objects.create(
                    user=request.user, content=content, community=target_community,
                    university=profile.university, image=request.FILES.get('image')
                )

            messages.success(request, f"הפוסט פורסם ב{target_community.name}! ✨")
            return redirect(f"{reverse('community_feed')}?community={target_community.id}")

    suggested_communities = Community.objects.filter(university=profile.university).exclude(
        members=request.user).order_by('?')[:3] if profile.university else Community.objects.none()

    context = {
        'posts': posts,
        'my_communities': my_communities,
        'current_community': current_community,
        'suggested_communities': suggested_communities,
        'university': profile.university,
    }
    return render(request, 'core/community_feed.html', context)


@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    community.members.add(request.user)
    messages.success(request, f"ברוך הבא ל{community.name}! הקהילה נוספה לפיד שלך.")
    return redirect(f"{reverse('community_feed')}?community={community.id}")


@login_required
def discover_communities(request):
    query = request.GET.get('q', '')
    all_communities = Community.objects.all()
    if query:
        all_communities = all_communities.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    context = {
        'global_comm': all_communities.filter(community_type='global'),
        'uni_comm': all_communities.filter(community_type='university'),
        'major_comm': all_communities.filter(community_type='major'),
        'query': query,
        'my_community_ids': request.user.joined_communities.values_list('id', flat=True)
    }
    return render(request, 'core/discover_communities.html', context)


@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        text = request.POST.get('text', '').strip()
        if text:
            comment = Comment.objects.create(post=post, user=request.user, text=text)
            user_img = None
            if hasattr(request.user, 'profile') and request.user.profile.profile_picture:
                user_img = request.user.profile.profile_picture.url
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'username': comment.user.username,
                'text': comment.text,
                'created_at': 'עכשיו',
                'user_img': user_img
            })
        return JsonResponse({'success': False, 'error': 'לא ניתן לפרסם תגובה ריקה.'}, status=400)
    return JsonResponse({'success': False, 'error': 'בקשה לא חוקית. נדרש POST.'}, status=400)


@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({'liked': liked, 'total_likes': post.likes.count()})
    return JsonResponse({'error': 'בקשה לא חוקית. נדרש POST.'}, status=400)
