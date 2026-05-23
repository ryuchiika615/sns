from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Post, Profile, Comment, GachaItem, Notification
import json
import random
import base64  # 🔮 画像を暗号化するために追加

NAMES_LIST = ["しゅり", "さよちゃん", "あつき", "すばる", "たいき", "ゆいちゃん", "みおちゃん", "ゆっきー"]
WORDS_LIST = [
    "花菜を奪いし者", "モモちゃん依存症", "なんやかんや桃が好き", "一生童貞", "ガリガリ",
    "韓国のり顔の", "犯罪予備軍", "バ畜戦士", "意識高い系", "闇落ちした", "巨乳の", "貧乳の",
    "誰もが三度見する", "今は亡き", "月給２４万", "税金泥棒", "国の犬", "ちいかわより",
    "やっぱり僕は", "みかんから生まれし", "桃から生まれし", "３浪の", "ゲーマーの", "１留の",
    "夢はマイクワゾウスキー", "デカビタよりもオロナミンｃ", "前世がティッシュ", "歩くR18指定",
    "煩脳の塊", "親の顔より見た", "出会い厨の", "全裸待機中の", "賢者モードの", "童貞をこじらせた",
    "変態という名の紳士", "パパ活疑惑の", "息をするようにスベる", "令和の奇行種", "脳内お花畑の",
    "歩く公然わいせつ", "圧倒的モブ", "クソエイムの", "課金沼に沈みし", "金欠の", "遅刻魔",
    "メンヘラ製造機", "留年確定の", "クソザコなめくじ", "深夜テンションの", "西村店長に怒られし",
    "チームラボで迷子になった", "カリフォルニア帰りの", "松戸市代表"
]

AVATAR_PREFIXES = ["漆黒の", "紅蓮の", "深淵の", "狂気の", "神聖なる", "禁忌の", "超電磁", "終焉の", "次元の",
                   "絶対零度の", "封印されし", "黄金の", "虚無の", "黙示録の", "終末の"]
AVATAR_NOUNS = ["堕天使の翼", "邪王真眼", "暗黒龍", "魔導書", "幻影の残像", "聖剣", "異界の門", "混沌のオーラ",
                "業火の盾", "裏コード", "破壊神の眼光", "神の加護", "絶対障壁", "不死鳥の羽"]


# 🔮 画像ファイルをデータベース保存可能な文字列に変換するヘルパー関数
def file_to_base64(file):
    if file:
        encoded = base64.b64encode(file.read()).decode('utf-8')
        return f"data:{file.content_type};base64,{encoded}"
    return None


def format_study_time(minutes):
    if not minutes or minutes == 0:
        return "0分"
    h, m = minutes // 60, minutes % 60
    return f"{h}時間{m}分" if h > 0 and m > 0 else f"{h}時間" if h > 0 else f"{m}分"


@login_required
def index(request):
    search_query = request.GET.get('search', '')
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'new_title' in request.POST:
            new_title = request.POST.get('new_title')
            if profile.items.filter(name=new_title).exists():
                profile.current_title = new_title
                profile.save()
            return redirect('index')

        if 'comment_text' in request.POST:
            post = get_object_or_404(Post, id=request.POST.get('post_id'))
            Comment.objects.create(post=post, user=request.user, text=request.POST.get('comment_text'))
            if post.user != request.user:
                Notification.objects.create(recipient=post.user, sender=request.user, post=post,
                                            notification_type='reply')
            return redirect('index')

        if 'delete_post_id' in request.POST:
            get_object_or_404(Post, id=request.POST.get('delete_post_id'), user=request.user).delete()
            return redirect('index')

        content = request.POST.get('content')
        if content:
            # 📝 追加：その他が選ばれたら自由入力を採用
            s_select = request.POST.get('subject', 'その他')
            s_custom = request.POST.get('subject_custom', '').strip()
            subject = s_custom if s_select == 'その他' and s_custom else s_select

            minutes = int(request.POST.get('study_minutes', 0))
            img_base64 = file_to_base64(request.FILES.get('image'))  # 🔮 投稿画像をBase64化

            Post.objects.create(user=request.user, content=content, study_minutes=minutes, image=img_base64,
                                subject=subject)
            profile.points += minutes
            profile.save()
        return redirect('index')

    # ⚡ 爆速化：select_related と prefetch_related で1発で全データを取得（N+1問題の完全解決）
    base_query = Post.objects.select_related('user', 'user__profile').prefetch_related('liked_by', 'comments',
                                                                                       'comments__user')
    all_posts = base_query.filter(content__icontains=search_query).order_by(
        '-created_at') if search_query else base_query.all().order_by('-created_at')

    paginator = Paginator(all_posts, 20)
    posts = paginator.get_page(request.GET.get('page'))

    now = timezone.now()
    for post in posts:
        if hasattr(post.user, 'profile'):
            item = GachaItem.objects.filter(name=post.user.profile.current_title).first()
            post.current_rarity = item.rarity if item else 'N'
            av_item = GachaItem.objects.filter(name=post.user.profile.current_avatar).first()
            post.avatar_rarity = av_item.rarity if av_item else 'N'
        post.display_study_time = format_study_time(post.study_minutes)
        diff = now - post.created_at
        post.formatted_time = "たった今" if diff.seconds < 60 else f"{diff.seconds // 60}分前" if diff.seconds < 3600 else f"{diff.seconds // 3600}時間前" if diff.days == 0 else post.created_at.strftime(
            '%m/%d %H:%M')

    today = timezone.now().date()
    labels, data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%m/%d'))
        data.append(Post.objects.filter(user=request.user, created_at__date=day).aggregate(Sum('study_minutes'))[
                        'study_minutes__sum'] or 0)

    remaining_minutes = 0
    remaining_display = ""
    has_target = False
    if profile.target_date and profile.target_minutes > 0:
        has_target = True
        total_study = Post.objects.filter(user=request.user).aggregate(Sum('study_minutes'))['study_minutes__sum'] or 0
        remaining_minutes = max(0, profile.target_minutes - total_study)
        remaining_display = format_study_time(remaining_minutes)

    return render(request, 'sns/index.html', {
        'posts': posts, 'labels': json.dumps(labels), 'data': json.dumps(data),
        'search_query': search_query,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'has_target': has_target, 'remaining_display': remaining_display,
        'target_date': profile.target_date, 'target_total_display': format_study_time(profile.target_minutes)
    })


@login_required
def gacha(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    result_items = []
    error = None

    if request.method == 'POST':
        pull_count = 10 if 'gacha_10' in request.POST else 1
        cost = pull_count * 10
        if profile.points >= cost:
            profile.points -= cost
            for _ in range(pull_count):
                rand = random.randint(1, 10000000)
                rarity = 'SSR' if rand == 1 else 'SR' if rand <= 100000 else 'R' if rand <= 1500000 else 'N'
                generated_name = f"【アイコン】{random.choice(AVATAR_PREFIXES)}{random.choice(AVATAR_NOUNS)}" if random.choice(
                    [True, False]) else f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}" if random.choice(
                    [True, False]) else f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"
                result_item, _ = GachaItem.objects.get_or_create(name=generated_name, defaults={'rarity': rarity})
                result_items.append(result_item)
                profile.items.add(result_item)
            profile.save()
        else:
            error = 'ポイントが足りません！もっと勉強しよう！'

    return render(request, 'sns/gacha.html', {'result_items': result_items, 'points': profile.points, 'error': error,
                                              'unread_count': Notification.objects.filter(recipient=request.user,
                                                                                          is_read=False).count()})


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    owned_items = profile.items.all().order_by('-rarity')
    real_owned_titles = owned_items.exclude(name__contains="【アイコン】")

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile.display_name = request.POST.get('display_name')
            profile.bio = request.POST.get('bio')
            profile.department = request.POST.get('department')
            profile.theme_color = request.POST.get('theme_color', 'dark')
            t_date = request.POST.get('target_date')
            profile.target_date = t_date if t_date else None
            profile.target_minutes = int(request.POST.get('target_minutes', 0) or 0)

            # 🔮 写真アイコンをBase64文字列に変換して保存
            if 'icon' in request.FILES:
                profile.icon = file_to_base64(request.FILES['icon'])

            profile.save()
            return redirect('edit_profile')

        if 'new_avatar' in request.POST:
            new_avatar = request.POST.get('new_avatar')
            if owned_items.filter(name=new_avatar).exists():
                profile.current_avatar = new_avatar
                profile.save()
            return redirect('index')

        if 'custom_name' in request.POST:
            c_name, c_word, order = request.POST.get('custom_name'), request.POST.get('custom_word'), request.POST.get(
                'order')
            valid_names = [n for n in NAMES_LIST if any(n in item.name for item in real_owned_titles)]
            valid_words = [w for w in WORDS_LIST if any(w in item.name for item in real_owned_titles)]
            if c_name in valid_names and c_word in valid_words:
                full_title = f"{c_word}{c_name}" if order == 'reverse' else f"{c_name}{c_word}"
                max_rarity_val = 1
                rarity_map = {'N': 1, 'R': 2, 'SR': 3, 'SSR': 4}
                val_to_r = {1: 'N', 2: 'R', 3: 'SR', 4: 'SSR'}
                for item in real_owned_titles:
                    if c_name in item.name or c_word in item.name: max_rarity_val = max(max_rarity_val,
                                                                                        rarity_map.get(item.rarity, 1))
                new_item, _ = GachaItem.objects.get_or_create(name=full_title,
                                                              defaults={'rarity': val_to_r[max_rarity_val]})
                profile.items.add(new_item)
                profile.current_title = full_title
                profile.save()
                return redirect('index')

    owned_names = [n for n in NAMES_LIST if any(n in item.name for item in real_owned_titles)]
    owned_words = [w for w in WORDS_LIST if any(w in item.name for item in real_owned_titles)]
    current_item = GachaItem.objects.filter(name=profile.current_title).first()
    av_item = GachaItem.objects.filter(name=profile.current_avatar).first()

    return render(request, 'sns/edit_profile.html', {
        'my_items': list(real_owned_titles), 'my_avatars': owned_items.filter(name__contains="【アイコン】"),
        'current_rarity': current_item.rarity if current_item else 'N',
        'current_av_rarity': av_item.rarity if av_item else 'N',
        'owned_names': owned_names, 'owned_words': owned_words,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
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
        if post.user != request.user: Notification.objects.create(recipient=post.user, sender=request.user, post=post,
                                                                  notification_type='like')
    return redirect('index')


@login_required
def user_profile(request, username):
    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, username=username)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)

    base_user_posts = Post.objects.select_related('user', 'user__profile').prefetch_related('liked_by', 'comments',
                                                                                            'comments__user').filter(
        user=target_user).order_by('-created_at')
    paginator = Paginator(base_user_posts, 20)
    user_posts = paginator.get_page(request.GET.get('page'))
    for post in user_posts: post.display_study_time = format_study_time(post.study_minutes)

    is_following = my_profile.follows.filter(id=target_profile.id).exists() if (
        my_profile := Profile.objects.get_or_create(user=request.user)[0]) else False
    title_item = GachaItem.objects.filter(name=target_profile.current_title).first()
    av_item = GachaItem.objects.filter(name=target_profile.current_avatar).first()

    return render(request, 'sns/user_profile.html', {
        'target_user': target_user, 'target_profile': target_profile, 'user_posts': user_posts,
        'is_following': is_following, 'target_title_rarity': title_item.rarity if title_item else 'N',
        'target_av_rarity': av_item.rarity if av_item else 'N', 'followers_count': target_profile.followed_by.count(),
        'following_count': target_profile.follows.count(),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@login_required
def toggle_follow(request, username):
    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, username=username)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.user != target_user:
        if my_profile.follows.filter(id=target_profile.id).exists():
            my_profile.follows.remove(target_profile)
        else:
            my_profile.follows.add(target_profile)
            Notification.objects.create(recipient=target_user, sender=request.user, notification_type='follow')
    return redirect('user_profile', username=username)


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:30]
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'sns/notifications.html', {'notifications': notifs, 'unread_count': 0})


@login_required
def analytics_view(request):
    user = request.user
    subject_data = Post.objects.filter(user=user, study_minutes__gt=0).values('subject').annotate(
        total=Sum('study_minutes')).order_by('-total')
    pie_labels, pie_data = [item['subject'] for item in subject_data], [item['total'] for item in subject_data]
    subject_list = [{'name': item['subject'], 'display_time': format_study_time(item['total'])} for item in
                    subject_data]

    today, bar_labels, bar_data = timezone.now().date(), [], []
    for i in range(5, -1, -1):
        month, year = today.month - i, today.year
        while month <= 0: month += 12; year -= 1
        bar_labels.append(f"{year}年{month}月")
        bar_data.append(Post.objects.filter(user=user, created_at__year=year, created_at__month=month).aggregate(
            Sum('study_minutes'))['study_minutes__sum'] or 0)

    return render(request, 'sns/analytics.html', {
        'pie_labels': json.dumps(pie_labels), 'pie_data': json.dumps(pie_data), 'bar_labels': json.dumps(bar_labels),
        'bar_data': json.dumps(bar_data),
        'subject_list': subject_list, 'total_all_time_display': format_study_time(
            Post.objects.filter(user=user).aggregate(Sum('study_minutes'))['study_minutes__sum'] or 0),
        'unread_count': Notification.objects.filter(recipient=user, is_read=False).count(),
    })