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
    "夢はマイクワゾウスキー", "デカビタよりもオロナミンｃ", "前世がティッシュ", "歩くR18指定",
    "煩脳の塊", "親の顔より見た", "出会い厨の", "全裸待機中の", "賢者モードの", "童貞をこじらせた",
    "変態という名の紳士", "パパ活疑惑の", "息をするようにスベる", "令和の奇行種", "脳内お花畑の",
    "歩く公然わいせつ", "圧倒的モブ", "クソエイムの", "課金沼に沈みし", "金欠の", "遅刻魔",
    "メンヘラ製造機", "留年確定の", "クソザコなめくじ", "深夜テンションの", "西村店長に怒られし",
    "チームラボで迷子になった", "カリフォルニア帰りの", "松戸市代表"
]

# 🔮 新規追加：100種類以上の中二病アイコン用パーツ（15×14＝計210通りのアバターが自動生成されます）
AVATAR_PREFIXES = ["漆黒の", "紅蓮の", "深淵の", "狂気の", "神聖なる", "禁忌の", "超電磁", "終焉の", "次元の",
                   "絶対零度の", "封印されし", "黄金の", "虚無の", "黙示録の", "終末の"]
AVATAR_NOUNS = ["堕天使の翼", "邪王真眼", "暗黒龍", "魔導書", "幻影の残像", "聖剣", "異界の門", "混沌のオーラ",
                "業火の盾", "裏コード", "破壊神の眼光", "神の加護", "絶対障壁", "不死鳥の羽"]


@login_required
def index(request):
    search_query = request.GET.get('search', '')

    if request.method == 'POST':
        # 1. 称号の装備処理
        if 'new_title' in request.POST:
            new_title = request.POST.get('new_title')
            profile = request.user.profile
            if profile.items.filter(name=new_title).exists():
                profile.current_title = new_title
                profile.save()
            return redirect('index')

        # 2. コメント投稿の場合
        if 'comment_text' in request.POST:
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            Comment.objects.create(post=post, user=request.user, text=request.POST.get('comment_text'))
            return redirect('index')

        # 3. コメント削除の場合
        if 'delete_comment_id' in request.POST:
            comment_id = request.POST.get('delete_comment_id')
            comment = get_object_or_404(Comment, id=comment_id, user=request.user)
            comment.delete()
            return redirect('index')

        # ★ 新機能：投稿（勉強時間などの本体）の削除機能
        if 'delete_post_id' in request.POST:
            post_id = request.POST.get('delete_post_id')
            post = get_object_or_404(Post, id=post_id, user=request.user)
            post.delete()
            return redirect('index')

        # 4. 通常の投稿の場合
        content = request.POST.get('content')
        study_minutes = request.POST.get('study_minutes', 0)
        image = request.FILES.get('image')
        minutes = int(study_minutes) if study_minutes else 0

        Post.objects.create(user=request.user, content=content, study_minutes=minutes, image=image)
        profile = request.user.profile
        profile.points += minutes
        profile.save()
        return redirect('index')

    if search_query:
        posts = Post.objects.filter(content__icontains=search_query).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    now = timezone.now()
    for post in posts:
        # 称号のレア度を計算
        item = GachaItem.objects.filter(name=post.user.profile.current_title).first()
        post.current_rarity = item.rarity if item else 'N'

        # アイコン（アバター）のレア度を計算して投稿にセット
        av_item = GachaItem.objects.filter(name=post.user.profile.current_avatar).first()
        post.avatar_rarity = av_item.rarity if av_item else 'N'

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
        'posts': posts, 'labels': json.dumps(labels), 'data': json.dumps(data), 'search_query': search_query
    })


# ガチャ画面（称号 or 中二病アイコンが手に入る仕様）
@login_required
def gacha(request):
    profile = request.user.profile
    result_items = []
    error = None

    if request.method == 'POST':
        pull_count = 10 if 'gacha_10' in request.POST else 1
        cost = pull_count * 10

        if profile.points >= cost:
            profile.points -= cost
            for _ in range(pull_count):
                # 超・鬼畜確率設定（SSRは1000万分の1）
                rand = random.randint(1, 10000000)
                if rand == 1:
                    rarity = 'SSR'
                elif rand <= 100000:
                    rarity = 'SR'
                elif rand <= 1500000:
                    rarity = 'R'
                else:
                    rarity = 'N'

                # 称号かアイコン（50%の確率）かを決定
                if random.choice([True, False]):
                    # アイコンスキンアバターを自動生成
                    generated_name = f"【アイコン】{random.choice(AVATAR_PREFIXES)}{random.choice(AVATAR_NOUNS)}"
                else:
                    # 称号を自動生成
                    if random.choice([True, False]):
                        generated_name = f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}"
                    else:
                        generated_name = f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"

                result_item, created = GachaItem.objects.get_or_create(name=generated_name, defaults={'rarity': rarity})
                result_items.append(result_item)
                profile.items.add(result_item)

            profile.save()
        else:
            error = 'ポイントが足りません！もっと勉強しよう！'

    return render(request, 'sns/gacha.html', {
        'result_items': result_items, 'points': profile.points, 'error': error
    })


# プロフィール編集（称号と中二病アイコンを分けて、当てたものだけを装備制限！）
@login_required
def edit_profile(request):
    profile = request.user.profile
    owned_items = profile.items.all().order_by('-rarity')

    # 【アイコン専用】POSTでアバター変更が送られてきた場合
    if request.method == 'POST' and 'new_avatar' in request.POST:
        new_avatar = request.POST.get('new_avatar')
        if owned_items.filter(name=new_avatar).exists():
            profile.current_avatar = new_avatar
            profile.save()
        return redirect('index')

    # 【称号専用】パーツ錬成
    owned_names = set()
    owned_words = set()
    for item in owned_items:
        if "【アイコン】" not in item.name:
            for n in NAMES_LIST:
                if n in item.name: owned_names.add(n)
            for w in WORDS_LIST:
                if w in item.name: owned_words.add(w)

    if request.method == 'POST' and 'custom_name' in request.POST:
        c_name = request.POST.get('custom_name')
        c_word = request.POST.get('custom_word')
        order = request.POST.get('order')

        if c_name in owned_names and c_word in owned_words:
            full_title = f"{c_word}{c_name}" if order == 'reverse' else f"{c_name}{c_word}"
            max_rarity_val = 1
            rarity_map = {'N': 1, 'R': 2, 'SR': 3, 'SSR': 4}
            val_to_r = {1: 'N', 2: 'R', 3: 'SR', 4: 'SSR'}
            for item in owned_items:
                if c_name in item.name or c_word in item.name:
                    max_rarity_val = max(max_rarity_val, rarity_map.get(item.rarity, 1))

            new_item, created = GachaItem.objects.get_or_create(name=full_title,
                                                                defaults={'rarity': val_to_r[max_rarity_val]})
            profile.items.add(new_item)
            profile.current_title = full_title
            profile.save()
            return redirect('index')

    # アイコン変更フォーム削除に伴い、この部分は不要になります
    # if request.method == 'POST' and 'icon' in request.FILES:
    #     profile.icon = request.FILES['icon']
    #     profile.save()
    #     return redirect('index')

    # 称号用とアイコン用にコレクションを分ける
    my_titles = [i for i in owned_items if "【アイコン】" not in i.name]
    my_avatars = owned_items.filter(name__contains="【アイコン】")

    current_item = GachaItem.objects.filter(name=profile.current_title).first()
    current_rarity = current_item.rarity if current_item else 'N'

    av_item = GachaItem.objects.filter(name=profile.current_avatar).first()
    current_av_rarity = av_item.rarity if av_item else 'N'

    return render(request, 'sns/edit_profile.html', {
        'my_items': my_titles,
        'my_avatars': my_avatars,
        'current_rarity': current_rarity,
        'current_av_rarity': current_av_rarity,
        'owned_names': list(owned_names),
        'owned_words': list(owned_words)
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