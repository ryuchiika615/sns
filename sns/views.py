from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Post, Profile, Comment, GachaItem
import json
import random

# 共通の身内語録データ（ここに好きなだけ追加・編集できます！）
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
        if 'new_title' in request.POST:
            profile = request.user.profile
            profile.current_title = request.POST.get('new_title')
            profile.save()
            return redirect('index')

        if 'comment_text' in request.POST:
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            Comment.objects.create(
                post=post,
                user=request.user,
                text=request.POST.get('comment_text')
            )
            return redirect('index')

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


# ガチャ画面（事前データがなくてもその場でランダム自動生成する神機能付き）
@login_required
def gacha(request):
    profile = request.user.profile
    result_item = None
    error = None

    if request.method == 'POST':
        if profile.points >= 10:
            rand = random.randint(1, 100)
            if rand <= 1:
                rarity = 'SSR'
            elif rand <= 10:
                rarity = 'SR'
            elif rand <= 30:
                rarity = 'R'
            else:
                rarity = 'N'

            # まずは指定のレア度のアイテムがDBにあるか探す
            items = GachaItem.objects.filter(rarity=rarity)

            if items.exists():
                result_item = random.choice(items)
            else:
                # 【超重要】DBが空っぽなら、その場でリストから合体させて新しい景品を自動作成！
                if random.choice([True, False]):
                    generated_name = f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}"
                else:
                    generated_name = f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"

                # その場で景品データを作ってDBに登録
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


# プロフィール編集（自分たちで名前や語録を自由に選んで称号を作れる機能を追加！）
@login_required
def edit_profile(request):
    if request.method == 'POST':
        # 1. アイコン変更の処理
        if 'icon' in request.FILES:
            request.user.profile.icon = request.FILES['icon']
            request.user.profile.save()
            return redirect('index')

        # 2. 【新機能】パーツを選んでオリジナル称号を作る処理
        if 'custom_name' in request.POST and 'custom_word' in request.POST:
            selected_name = request.POST.get('custom_name')
            selected_word = request.POST.get('custom_word')
            order = request.POST.get('order')  # "normal" か "reverse"

            # 順番を逆にするかどうかの判定
            if order == "reverse":
                full_title = f"{selected_word}{selected_name}"  # 例：一生童貞しゅり
            else:
                full_title = f"{selected_name}{selected_word}"  # 例：しゅり一生童貞

            profile = request.user.profile
            profile.current_title = full_title
            profile.save()
            return redirect('index')

    my_items = request.user.profile.items.all().order_by('-rarity')

    return render(request, 'sns/edit_profile.html', {
        'my_items': my_items,
        'names': NAMES_LIST,
        'words': WORDS_LIST
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