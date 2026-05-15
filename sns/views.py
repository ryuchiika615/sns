from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Post, Profile, Comment, GachaItem
import json
import random


@login_required
def index(request):
    search_query = request.GET.get('search', '')

    if request.method == 'POST':
        # 1. 称号（タイトル）の装備処理を追加！
        if 'new_title' in request.POST:
            profile = request.user.profile
            profile.current_title = request.POST.get('new_title')
            profile.save()
            return redirect('index')

        # 2. コメント投稿の場合
        if 'comment_text' in request.POST:
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            Comment.objects.create(
                post=post,
                user=request.user,
                text=request.POST.get('comment_text')
            )
            return redirect('index')

        # 3. 通常の投稿の場合
        content = request.POST.get('content')
        study_minutes = request.POST.get('study_minutes', 0)
        image = request.FILES.get('image')
        minutes = int(study_minutes) if study_minutes else 0

        Post.objects.create(
            user=request.user,
            content=content,
            study_minutes=minutes,
            image=image
        )

        profile = request.user.profile
        profile.points += minutes
        profile.save()
        return redirect('index')

    if search_query:
        posts = Post.objects.filter(content__icontains=search_query).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    recent_posts = Post.objects.filter(user=request.user).order_by('created_at')[:7]
    labels = [p.created_at.strftime('%m/%d') for p in recent_posts]
    data = [p.study_minutes for p in recent_posts]

    return render(request, 'sns/index.html', {
        'posts': posts,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'search_query': search_query
    })


# ガチャ画面
@login_required
def gacha(request):
    profile = request.user.profile
    result_item = None
    error = None

    if request.method == 'POST':
        if profile.points >= 10:
            profile.points -= 10
            rand = random.randint(1, 100)
            if rand <= 1:
                rarity = 'SSR'
            elif rand <= 10:
                rarity = 'SR'
            elif rand <= 30:
                rarity = 'R'
            else:
                rarity = 'N'

            items = GachaItem.objects.filter(rarity=rarity)
            if items.exists():
                result_item = random.choice(items)
                profile.items.add(result_item)
                profile.save()
            else:
                result_item = random.choice(GachaItem.objects.all())
                profile.items.add(result_item)
                profile.save()
        else:
            error = 'ポイントが足りません！あと少し勉強しよう！'

    return render(request, 'sns/gacha.html', {
        'result_item': result_item,
        'points': profile.points,
        'error': error
    })


# プロフィール編集（称号一覧の表示も兼ねる）
@login_required
def edit_profile(request):
    if request.method == 'POST':
        if 'icon' in request.FILES:
            request.user.profile.icon = request.FILES['icon']
            request.user.profile.save()
        return redirect('index')

    # 自分が持っているガチャアイテムを全部取得して画面に送る
    my_items = request.user.profile.items.all().order_by('-rarity')
    return render(request, 'sns/edit_profile.html', {'my_items': my_items})


def logout_view(request):
    logout(request)
    return redirect('login')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'sns/signup.html', {'form': form})


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.liked_by.all():
        post.liked_by.remove(request.user)
    else:
        post.liked_by.add(request.user)
    return redirect('index')