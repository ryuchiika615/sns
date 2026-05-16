from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Post, Profile, Comment, GachaItem
import json
import random

# 共通の身内語録データ
NAMES_LIST = ["しゅり", "さよちゃん", "あつき", "すばる", "たいき", "ゆいちゃん", "みおちゃん", "ゆっきー"]
WORDS_LIST = [
    "花菜を奪いし者", "モモちゃん依存症", "なんやかんや桃が好き", "一生童貞", "ガリガリ",
    "韓国のり顔の", "犯罪予備軍", "バ畜戦士", "意識高い系", "闇落ちした", "巨乳の", "貧乳の",
    "誰もが三度見する", "今は亡き", "月給２４万", "税金泥棒", "国の犬", "ちいかわより",
    "やっぱり僕は", "みかんから生まれし", "桃から生まれし", "３浪の", "ゲーマーの", "１留の",
    "夢はマイクワゾウスキー", "デカビタよりもオロナミンｃ"
]


@login_required
def index(request):
    search_query = request.GET.get('search', '')

    if request.method == 'POST':
        # 1. 称号の装備処理（自分が本当に持っているか厳格にチェック！）
        if 'new_title' in request.POST:
            new_title = request.POST.get('new_title')
            profile = request.user.profile
            # ガチャで当てて所有しているアイテムの中に、その称号がある場合のみ装備を許可
            if profile.items.filter(name=new_title).exists():
                profile.current_title = new_title
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

    # 投稿一覧の取得
    if search_query:
        posts = Post.objects.filter(content__icontains=search_query).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    # 【重要新機能】各投稿に「称号のレア度」と「きめ細かい投稿時間」をセットする
    now = timezone.now()
    for post in posts:
        # レア度の判定
        item = GachaItem.objects.filter(name=post.user.profile.current_title).first()
        post.current_rarity = item.rarity if item else 'N'

        # タイムスタンプ（〇分前など）の計算
        diff = now - post.created_at
        if diff.days > 0:
            post.formatted_time = post.created_at.strftime('%m/%d %H:%M')
        elif diff.seconds < 60:
            post.formatted_time = "たった今"
        elif diff.seconds < 3600:
            post.formatted_time = f"{diff.seconds // 60}分前"
        else:
            post.formatted_time = f"{diff.seconds // 3600}時間前"

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
            rand = random.randint(1, 100)
            if rand <= 2:  # SSRは2%の超激レア仕様！
                rarity = 'SSR'
            elif rand <= 15:
                rarity = 'SR'
            elif rand <= 40:
                rarity = 'R'
            else:
                rarity = 'N'

            items = GachaItem.objects.filter(rarity=rarity)

            if items.exists():
                result_item = random.choice(items)
            else:
                # DBになければ、その場で身内語録リストから合体させて新しい称号を自動錬成！
                if random.choice([True, False]):
                    generated_name = f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}"
                else:
                    generated_name = f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"

                result_item = GachaItem.objects.create(name=generated_name, rarity=rarity)

            if result_item:
                profile.points -= 10
                profile.items.add(result_item)
                profile.save()
        else:
            error = 'ポイントが足りません！あと少し勉強しよう！'

    return render(request, 'sns/gacha.html', {
        'result_item': result_item,
        'points': profile.points,
        'error': error
    })


# プロフィール編集（コレクションから選ぶだけのガチ仕様に変更）
@login_required
def edit_profile(request):
    if request.method == 'POST':
        if 'icon' in request.FILES:
            request.user.profile.icon = request.FILES['icon']
            request.user.profile.save()
        return redirect('index')

    # 自分がこれまでにガチャで当てて所有している称号の一覧
    my_items = request.user.profile.items.all().order_by('-rarity')

    # 現在セットしている称号のレア度を調べる
    current_title = request.user.profile.current_title
    current_item = GachaItem.objects.filter(name=current_title).first()
    current_rarity = current_item.rarity if current_item else 'N'

    return render(request, 'sns/edit_profile.html', {
        'my_items': my_items,
        'current_rarity': current_rarity
    })


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