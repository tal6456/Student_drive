
"""
קובץ SOCIAL: ניהול הלוגיקה של מערכת הקהילות (Communities)
=====================================================

מה זה בכלל קובץ Views ב-Django?
--------------------------------
VIEWS הוא המח של האפליקציה.
הוא מתווך בין הדפדפן לבין הטהלאות נתונים MODELS.
1. לקבל בקשות (Requests) מהמשתמש.
2. לבצע לוגיקה עסקית (חישובים, בדיקות הרשאות, שליפת נתונים).
3. להחזיר תגובה (Response) - בדרך כלל דף HTML מעובד או נתונים בפורמט JSON (במקרה של AJAX).

מטרת הקובץ הספציפי הזה (social.py):
--------------------------------------------
קובץ זה הופרד מה-views הראשי כדי לרכז את כל הפונקציונליות החברתית של הפרויקט.
הוא מטפל ב:
* ניהול הפיד המרכזי (community_feed): הצגת פוסטים מותאמים אישית לפי מוסד הלימודים של הסטודנט.
* יצירת תוכן מגוון: תמיכה בפוסטים רגילים, פוסטים של וידאו ופוסטים של Marketplace (יד שנייה).
* אינטראקציות חברתיות: מנגנון לייקים (Likes) ותגובות (Comments) מבוסס AJAX לחוויית משתמש מהירה.
* גילוי קהילות: חיפוש והצטרפות לקהילות חדשות (גלובליות, מוסדיות או לפי תחום לימוד).
* אופטימיזציה: שימוש ב-select_related ו-prefetch_related למניעת עומס על מסד הנתונים (בעיית N+1).
"""



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q

# ייבוא רק של המודלים הקשורים לקהילה
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
        # יצירת קהילה חכמה אם היא חסרה
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

        # מוודאים שהמשתמש חבר בקהילה
        if current_community not in my_communities:
            current_community.members.add(request.user)

    # --- התיקון הקריטי להזחות ולמניעת N+1 ---
    if current_community:
        posts = Post.objects.filter(community=current_community).select_related(
            'user', 'user__profile', 'university', 'community'
        ).prefetch_related('likes', 'comments')
    else:
        posts = Post.objects.none()

    # סינון לפי סוג הפוסט (Marketplace וכו')
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