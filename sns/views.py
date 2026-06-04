import base64
import json
import random
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Comment, GachaItem, Notification, Post, Profile, UserLoginSession


def health_check(request):
    return HttpResponse("ok", content_type="text/plain")


NAMES_LIST = ["リュウ", "ミナ", "ソラ", "ハル", "ユイ", "レン", "アオ", "ナギ"]
WORDS_LIST = [
    "限界突破の", "集中の", "知識を喰らう", "夜明けの", "継続する", "答案を砕く",
    "ノートの守護者", "暗記特化", "計算疾走", "眠気討伐", "努力型", "図書館の",
]
AVATAR_PREFIXES = ["星屑の", "深夜の", "黄金の", "透明な", "覚醒した", "ふわふわ"]
AVATAR_NOUNS = ["翼", "魔眼", "オーラ", "王冠", "守護獣", "勉強ねこ", "集中うさぎ"]
LEGENDARY_PREFIXES = ["星海を裂く", "終焉を照らす", "天穹を統べる", "不可視の", "黎明の"]
LEGENDARY_NOUNS = ["観測者", "時間術師", "学習賢者", "記憶の王冠", "答案破壊者"]
CUTE_PREFIXES = ["もちもち", "きらきら", "ふわふわ", "ほめ上手な", "ゆるかわ"]
CUTE_NOUNS = ["勉強ねこ", "集中うさぎ", "ノート妖精", "ごほうびパンダ", "暗記ハムスター"]
ANIMAL_PREFIXES = ["疾走する", "夜更けの", "図書館の", "森の", "黄金の"]
ANIMAL_NOUNS = ["きつね先生", "ふくろう博士", "こぐま隊長", "しばいぬ賢者", "ペンギン参謀"]

NAMES_LIST = [
    "ゆいちゃん", "たいき", "あつき", "みおちゃん", "すばる", "ゆっきー", "さよちゃん", "しゅり",
    "りゅう", "みな", "そら", "はる", "れん", "あお", "なぎ",
]
WORDS_LIST = [
    "レポート未提出の", "単位を落とせし", "再履修のプロ", "課題に追われる", "電機大の良心", "北千住の支配者",
    "数学で詰んだ", "過去問を渇望する", "試験前日に徹夜する", "フル単の奇跡", "出席日数ギリギリの",
    "教授に目をつけられし", "研究室に引きこもる", "学食のカレーを愛する", "3号館で迷子になった",
    "線形代数で爆死した", "プログラミング課題を丸写しする", "意識だけは高い留年候補", "通学路がほぼ旅",
    "プレデターになれない", "万年ブロンズの", "クソエイムを極めし", "ウルトを無駄打ちする",
    "スプラで煽られる", "常にデスしている", "キャリーされ待ちの", "味方にブチギレる",
    "ガチホコを逆走する", "マイクラで全ロスした", "マリオメーカーで沼る", "回線落ちの帝王",
    "伝説の戦犯", "プレイヤースキル最底辺の", "ワンオペで崩壊する", "労働の奴隷", "残業代が出ない",
    "バイトリーダーを気取る", "レジ締めが合わない", "クレーマーを引き寄せる", "給料日前に干からびる",
    "貯金残高3桁の", "100円ローソン通いの", "もやし生活の", "奢られ待ちの天才", "財布を家に忘れる",
    "常に金ないが口癖の", "借金まみれの", "経済力皆無の", "Twitterに生息する", "ネット弁慶の",
    "匿名でしかイキれない", "いいねを渇望する", "炎上寸前の", "リプ欄でレスバする", "黒歴史を量産せし",
    "厨二病を拗らせた", "右手が疼く", "邪気眼の使い手", "闇の組織に追われる", "限界オタクの",
    "推しに全財産を貢ぐ", "液晶画面に恋する", "1日20時間画面を見る", "自称インフルエンサーの",
    "バズる幻覚を見る", "存在が放送事故の", "息をするだけで面白い", "絶望的に服のセンスがない",
    "常に寝不足の", "偏食の極み", "エナジードリンク中毒の", "三日坊主のエース", "言い訳の達人",
    "責任転嫁のプロ", "プライドだけはエベレストな", "口だけは達者な", "行動力を失いし",
    "部屋がゴミ屋敷の", "忘れ物の神様", "信頼残高マイナスの", "陽キャのフリをした",
    "LINEの返信が遅すぎる", "既読無視の常習犯", "嫉妬の化身", "すぐ病む", "メンヘラの極み",
    "恋愛初心者以下の", "独占欲の塊", "記念日を忘れる", "愛が重すぎる", "朝起きられない",
    "布団から出られない", "2度寝のファンタジスタ", "遅刻の常連", "時間を守る気がない",
    "常にギリギリを生きる", "奇跡待ちの", "就活を現実逃避する", "面接で頭が真っ白になる",
    "お祈りメールのコレクター", "自己分析で絶望する", "実家でイキる", "家族のパシリ",
    "親の脛を齧り尽くす", "ペーパードライバーの", "常に裏コードを入力している", "魔導書を枕にする",
    "混沌のオーラを纏う", "封印されし左手が暴れる", "黙示録の予言者", "終末を告げるもの",
    "神の加護を失いし", "令和の怪物", "世紀の大悪党", "希代の詐欺師", "期待の新人（仮）",
    "自称・天才エンジニア", "世界を救いそうにない勇者", "魔王のパシリ", "ただの一般人A",
    "西村店長に怒られし", "チームラボで迷子になった", "息をするようにスベる", "深夜テンションの",
    "松戸市代表", "カリフォルニア帰りの", "3浪の", "1留の", "留年確定の", "バ畜戦士",
    "月給24万", "金欠の", "課金沼に沈みし", "花菜を奪いし者", "令和の奇行種",
    "脳内お花畑の", "意識高い系", "圧倒的モブ", "メンヘラ製造機", "前世がティッシュ",
    "夢はマイクワゾウスキー", "みかんから生まれし", "桃から生まれし", "韓国のり顔の",
]
NOUNS_LIST = [
    "支配者", "プロ", "帝王", "奇跡", "良心", "戦士", "候補", "常習犯", "コレクター", "使い手",
    "観測者", "勇者", "パシリ", "一般人A", "天才", "怪物", "大悪党", "詐欺師", "落ちこぼれ",
    "ファンタジスタ", "エース", "達人", "神様", "化身", "塊", "奴隷", "リーダー", "モブ",
    "奇行種", "放送事故", "留年候補", "戦犯", "ブロンズ", "インフルエンサー",
]
AVATAR_PREFIXES = ["星屑の", "深夜の", "黒鉄の", "透明な", "覚醒した", "まばゆい"]
AVATAR_NOUNS = ["翼", "魔導書", "オーラ", "王冠", "守護印", "勉強ねこ", "集中うさぎ"]
LEGENDARY_PREFIXES = ["星海を裂く", "終焉を照らす", "天空を統べる", "不可視の", "黒炎の"]
LEGENDARY_NOUNS = ["観測者", "時間術師", "学習賢者", "記憶の王冠", "答案破壊者"]
CUTE_PREFIXES = ["もちもち", "きらきら", "ふわふわ", "ほめ上手な", "ゆるかわ"]
CUTE_NOUNS = ["勉強ねこ", "集中うさぎ", "ノート妖精", "ごほうびパンダ", "暗記ハムスター"]
ANIMAL_PREFIXES = ["疾走する", "夜更けの", "図書館の", "森の", "黒鉄の"]
ANIMAL_NOUNS = ["きつね先生", "ふくろう騎士", "こぐま隊長", "しろくま賢者", "ペンギン参謀"]

SHOP_CATALOG = {
    "title": {
        "N": NAMES_LIST + NOUNS_LIST[:10] + WORDS_LIST[:12],
        "R": WORDS_LIST[12:45] + NOUNS_LIST[10:18],
        "SR": WORDS_LIST[45:75] + NOUNS_LIST[18:26],
        "SSR": WORDS_LIST[75:105] + NOUNS_LIST[26:],
        "UR": WORDS_LIST[105:130] + ["終焉を照らす観測者", "天空を統べる学習賢者", "不可視の時間術師"],
        "LR": WORDS_LIST[130:] + ["黒炎の記憶の王冠", "星海を裂く答案破壊者", "終焉を照らす時間術師"],
    },
    "icon": {
        "N": ["【アイコン】努力の羽根", "【アイコン】ノートの星", "【アイコン】集中リング"],
        "R": ["【アイコン】夜更けの翼", "【アイコン】青い魔導書", "【アイコン】覚醒バッジ"],
        "SR": ["【アイコン】黒鉄の王冠", "【アイコン】星屑のオーラ", "【アイコン】透明な守護印"],
        "SSR": ["【アイコン】黄金の集中冠", "【アイコン】黒炎の紋章", "【アイコン】疾走する魔導書"],
        "UR": ["【アイコン】天空の観測輪", "【アイコン】終焉のオーラ", "【アイコン】不可視の翼"],
        "LR": ["【アイコン】星海を裂く王冠", "【アイコン】黒炎の神印", "【アイコン】答案破壊の光輪"],
    },
}

SUBJECT_COLORS = [
    "#1877f2", "#ff6b6b", "#20c997", "#f59f00", "#845ef7", "#12b886",
    "#e64980", "#15aabf", "#fd7e14", "#5c7cfa", "#82c91e", "#be4bdb",
]
RARITY_ORDER = {"N": 1, "R": 2, "SR": 3, "SSR": 4, "UR": 5, "LR": 6}
RARITY_BY_VALUE = {value: key for key, value in RARITY_ORDER.items()}
SELL_VALUES = {"N": 1, "R": 4, "SR": 15, "SSR": 60, "UR": 180, "LR": 650}
BUY_COSTS = {"N": 5, "R": 15, "SR": 60, "SSR": 240, "UR": 720, "LR": 2600}
RARITY_LABELS = {"N": "N", "R": "R", "SR": "SR", "SSR": "SSR", "UR": "UR", "LR": "LR"}
GACHA_COST_PER_PULL = 10
GACHA_COOLDOWN_SECONDS = 2


def file_to_base64(file):
    if file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
        return f"data:{file.content_type};base64,{encoded}"
    return None


def format_study_time(minutes):
    minutes = minutes or 0
    h = minutes // 60
    m = minutes % 60
    if h > 0 and m > 0:
        return f"{h}時間{m}分"
    if h > 0:
        return f"{h}時間"
    return f"{m}分"


def display_name(user):
    profile = getattr(user, "profile", None)
    return (profile.display_name if profile and profile.display_name else user.username)


def account_label(user):
    return f"{display_name(user)} @{user.username}"


def subject_color(subject):
    total = sum(ord(ch) for ch in (subject or "その他"))
    return SUBJECT_COLORS[total % len(SUBJECT_COLORS)]


def is_site_admin(user):
    return user.is_authenticated and (user.is_superuser or user.username == settings.SITE_ADMIN_USERNAME)


def selected_date_range(request, default_days=30, max_days=366):
    today = timezone.localdate()
    default_start = today - timedelta(days=default_days - 1)
    start = parse_date(request.GET.get("start", "")) or default_start
    end = parse_date(request.GET.get("end", "")) or today
    if end > today:
        end = today
    if start > end:
        start = end
    if (end - start).days > max_days:
        start = end - timedelta(days=max_days)
    return start, end


def set_post_date(post, study_date):
    today = timezone.localdate()
    if study_date == today:
        dt = timezone.now()
    else:
        dt = timezone.make_aware(datetime.combine(study_date, time(hour=12)), timezone.get_current_timezone())
    Post.objects.filter(id=post.id).update(created_at=dt)
    post.created_at = dt


def local_post_time(post):
    return timezone.localtime(post.created_at)


def is_icon_item(item):
    return item.name.startswith("【アイコン】") or "アイコン" in item.name or "繧｢繧､繧ｳ繝ｳ" in item.name


def is_refined_item(item):
    return item.name.startswith("精錬:") or item.name.startswith("邊ｾ骭ｬ:")


def item_display_name(item_or_name):
    name = item_or_name.name if hasattr(item_or_name, "name") else str(item_or_name)
    return name.replace("精錬:", "").replace("邊ｾ骭ｬ:", "")


def owned_title_parts(items):
    display_names = [item_display_name(item) for item in items]
    return {
        "words": [word for word in WORDS_LIST if any(word in name for name in display_names)],
        "nouns": [noun for noun in NOUNS_LIST if any(noun in name for name in display_names)],
        "names": [name for name in NAMES_LIST if any(name in title for title in display_names)],
    }


def refined_part_rarity(part, items):
    value = 1
    for item in items:
        if part and part in item_display_name(item):
            value = max(value, RARITY_ORDER.get(item.rarity, 1))
    return value


def shop_item_name(rarity):
    if rarity in ["UR", "LR"]:
        return f"{random.choice(LEGENDARY_PREFIXES)}{random.choice(LEGENDARY_NOUNS)}"
    if rarity == "SSR":
        return f"{random.choice(CUTE_PREFIXES + ANIMAL_PREFIXES)}{random.choice(CUTE_NOUNS + ANIMAL_NOUNS)}"
    if random.choice([True, False]):
        return f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}"
    return f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"


def gacha_title_name(rarity):
    if rarity == "N":
        return random.choice(NAMES_LIST + NOUNS_LIST[:10] + WORDS_LIST[:20])
    if rarity == "R":
        return random.choice(WORDS_LIST[20:65] + NOUNS_LIST[10:18])
    if rarity == "SR":
        return random.choice(WORDS_LIST[65:100] + NOUNS_LIST[18:26])
    if rarity == "SSR":
        return random.choice(WORDS_LIST[100:125] + NOUNS_LIST[26:] + [f"{random.choice(WORDS_LIST[:60])}{random.choice(NAMES_LIST)}"])
    if rarity == "UR":
        return random.choice(WORDS_LIST[125:] + ["終焉を照らす観測者", "天空を統べる学習賢者", "不可視の時間術師"])
    return random.choice(["黒炎の記憶の王冠", "星海を裂く答案破壊者", "終焉を照らす時間術師"] + WORDS_LIST[-20:])


def roll_gacha_item():
    rand = random.randint(1, 10000000)
    if rand == 1:
        rarity = "LR"
    elif rand <= 1200:
        rarity = "UR"
    elif rand <= 70000:
        rarity = "SSR"
    elif rand <= 450000:
        rarity = "SR"
    elif rand <= 2000000:
        rarity = "R"
    else:
        rarity = "N"

    if random.random() < 0.38:
        generated_name = f"【アイコン】{random.choice(ANIMAL_PREFIXES)}{random.choice(ANIMAL_NOUNS)}"
    elif random.random() < 0.38:
        generated_name = f"【アイコン】{random.choice(AVATAR_PREFIXES)}{random.choice(AVATAR_NOUNS)}"
    else:
        generated_name = gacha_title_name(rarity)

    return GachaItem.objects.get_or_create(name=generated_name, defaults={"rarity": rarity})[0]


def sell_items(profile, items):
    total = 0
    protected = {profile.current_title, profile.current_avatar}
    for item in items:
        if item.name in protected or is_refined_item(item):
            continue
        total += SELL_VALUES.get(item.rarity, 0)
        profile.items.remove(item)
    if total:
        profile.exchange_points += total
        profile.save(update_fields=["exchange_points"])
    return total


def build_subject_rows(queryset):
    rows = list(
        queryset.values("subject")
        .annotate(total=Sum("study_minutes"), count=Count("id"))
        .order_by("-total")[:12]
    )
    for row in rows:
        row["display_time"] = format_study_time(row["total"])
        row["color"] = subject_color(row["subject"])
    return rows


def build_stacked_week_chart(user):
    today = timezone.localdate()
    start = today - timedelta(days=6)
    labels = [(start + timedelta(days=i)).strftime("%m/%d") for i in range(7)]
    subjects = list(
        Post.objects.filter(user=user, created_at__date__gte=start, study_minutes__gt=0)
        .values("subject")
        .annotate(total=Sum("study_minutes"))
        .order_by("-total")[:6]
    )
    subject_names = [item["subject"] for item in subjects]
    raw = (
        Post.objects.filter(user=user, created_at__date__gte=start, subject__in=subject_names)
        .annotate(day=TruncDate("created_at"))
        .values("day", "subject")
        .annotate(total=Sum("study_minutes"))
    )
    totals = {(item["day"], item["subject"]): item["total"] or 0 for item in raw}
    datasets = []
    for subject in subject_names:
        datasets.append({
            "label": subject,
            "data": [totals.get((start + timedelta(days=i), subject), 0) for i in range(7)],
            "backgroundColor": subject_color(subject),
            "borderRadius": 5,
        })
    if not datasets:
        datasets.append({
            "label": "勉強時間",
            "data": [0 for _ in range(7)],
            "backgroundColor": "#1877f2",
            "borderRadius": 5,
        })
    return labels, datasets


@login_required
def index(request):
    search_query = request.GET.get("search", "")
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if "new_title" in request.POST:
            new_title = request.POST.get("new_title")
            if profile.items.filter(name=new_title).exists():
                profile.current_title = new_title
                profile.save(update_fields=["current_title"])
            return redirect("index")

        if "comment_text" in request.POST:
            post = get_object_or_404(Post, id=request.POST.get("post_id"))
            Comment.objects.create(post=post, user=request.user, text=request.POST.get("comment_text"))
            if post.user != request.user:
                Notification.objects.create(
                    recipient=post.user, sender=request.user, post=post, notification_type="reply"
                )
            return redirect("index")

        if "delete_comment_id" in request.POST:
            comment = get_object_or_404(Comment, id=request.POST.get("delete_comment_id"), user=request.user)
            comment.delete()
            return redirect("index")

        if "delete_post_id" in request.POST:
            post = get_object_or_404(Post, id=request.POST.get("delete_post_id"), user=request.user)
            post.delete()
            return redirect("index")

        content = request.POST.get("content")
        if content:
            subject = request.POST.get("subject", "その他").strip() or "その他"
            study_minutes = request.POST.get("study_minutes", 0)
            minutes = int(study_minutes) if study_minutes else 0
            study_date = parse_date(request.POST.get("study_date", "")) or timezone.localdate()
            image_base64 = file_to_base64(request.FILES.get("image"))
            post = Post.objects.create(
                user=request.user,
                content=content,
                study_minutes=minutes,
                image=image_base64,
                subject=subject,
            )
            set_post_date(post, study_date)
            profile.points += minutes
            profile.save(update_fields=["points"])
        return redirect("index")

    base_query = Post.objects.select_related("user", "user__profile").prefetch_related(
        "liked_by", "comments", "comments__user"
    )
    all_posts = base_query.filter(content__icontains=search_query) if search_query else base_query.all()
    all_posts = all_posts.order_by("-created_at")

    paginator = Paginator(all_posts, 10)
    posts = paginator.get_page(request.GET.get("page"))
    posts.object_list = list(posts.object_list)

    gacha_names = set()
    for post in posts.object_list:
        if hasattr(post.user, "profile"):
            gacha_names.add(post.user.profile.current_title)
            gacha_names.add(post.user.profile.current_avatar)
    rarity_by_name = {item.name: item.rarity for item in GachaItem.objects.filter(name__in=gacha_names)}

    now = timezone.now()
    for post in posts.object_list:
        if hasattr(post.user, "profile"):
            post.current_rarity = rarity_by_name.get(post.user.profile.current_title, "N")
            post.avatar_rarity = rarity_by_name.get(post.user.profile.current_avatar, "N")
            post.current_title_display = item_display_name(post.user.profile.current_title)
        else:
            Profile.objects.get_or_create(user=post.user)
            post.current_rarity = "N"
            post.avatar_rarity = "N"
            post.current_title_display = ""
        post.display_study_time = format_study_time(post.study_minutes)
        post.subject_color = subject_color(post.subject)
        post.author_label = account_label(post.user)
        post_local_time = local_post_time(post)
        diff = now - post.created_at
        if diff.days > 0:
            post.formatted_time = post_local_time.strftime("%m/%d %H:%M")
        elif diff.seconds < 60:
            post.formatted_time = "たった今"
        elif diff.seconds < 3600:
            post.formatted_time = f"{diff.seconds // 60}分前"
        else:
            post.formatted_time = f"{diff.seconds // 3600}時間前"

    labels, chart_datasets = build_stacked_week_chart(request.user)
    total_this_week = sum(sum(dataset["data"]) for dataset in chart_datasets)

    remaining_display = ""
    has_target = False
    if profile.target_date and profile.target_minutes > 0:
        has_target = True
        total_study = Post.objects.filter(user=request.user).aggregate(Sum("study_minutes"))["study_minutes__sum"] or 0
        remaining_display = format_study_time(max(profile.target_minutes - total_study, 0))

    return render(request, "sns/index.html", {
        "posts": posts,
        "labels": json.dumps(labels),
        "chart_datasets": json.dumps(chart_datasets),
        "search_query": search_query,
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
        "has_target": has_target,
        "remaining_display": remaining_display,
        "target_date": profile.target_date,
        "target_total_display": format_study_time(profile.target_minutes),
        "today": timezone.localdate(),
        "total_this_week_display": format_study_time(total_this_week),
    })


@login_required
def gacha(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    result_items = []
    error = None
    summary = None

    if request.method == "POST":
        now_ts = timezone.now().timestamp()
        last_gacha_ts = request.session.get("last_gacha_ts", 0)
        if now_ts - last_gacha_ts < GACHA_COOLDOWN_SECONDS:
            error = "?????????????????????????????"
            return render(request, "sns/gacha.html", {
                "result_items": result_items,
                "points": profile.points,
                "error": error,
                "summary": summary,
                "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
            })

        if "gacha_100" in request.POST:
            pull_count = 100
        elif "gacha_10" in request.POST:
            pull_count = 10
        else:
            pull_count = 1

        cost = pull_count * GACHA_COST_PER_PULL
        if profile.points >= cost:
            request.session["last_gacha_ts"] = now_ts
            profile.points -= cost
            rarity_counts = {rarity: 0 for rarity in ["N", "R", "SR", "SSR", "UR", "LR"]}
            for _ in range(pull_count):
                result_item = roll_gacha_item()
                result_items.append(result_item)
                rarity_counts[result_item.rarity] = rarity_counts.get(result_item.rarity, 0) + 1
            if result_items:
                profile.items.add(*result_items)
            profile.save(update_fields=["points"])
            summary = [
                {"rarity": rarity, "count": rarity_counts[rarity]}
                for rarity in ["LR", "UR", "SSR", "SR", "R", "N"]
                if rarity_counts[rarity]
            ]
        else:
            error = "????????????????????????????"

    return render(request, "sns/gacha.html", {
        "result_items": result_items,
        "points": profile.points,
        "error": error,
        "summary": summary,
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })


@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    owned_items = profile.items.all().order_by("-rarity")
    icon_query = Q(name__contains="【アイコン】") | Q(name__contains="繧｢繧､繧ｳ繝ｳ")
    real_owned_titles = owned_items.exclude(icon_query)

    if request.method == "POST":
        if "update_profile" in request.POST:
            requested_username = (request.POST.get("username") or "").strip()
            username_error = None
            if requested_username and requested_username != request.user.username:
                if User.objects.filter(username=requested_username).exclude(id=request.user.id).exists():
                    username_error = "このIDはすでに使われています。別のIDにしてください。"
                else:
                    request.user.username = requested_username
                    request.user.save(update_fields=["username"])

            profile.display_name = request.POST.get("display_name")
            profile.bio = request.POST.get("bio")
            profile.department = request.POST.get("department")
            profile.theme_color = request.POST.get("theme_color", "dark")
            profile.target_date = request.POST.get("target_date") or None
            profile.target_minutes = int(request.POST.get("target_minutes") or 0)
            if "icon" in request.FILES:
                profile.icon = file_to_base64(request.FILES["icon"])
            profile.save()
            if username_error:
                current_item = GachaItem.objects.filter(name=profile.current_title).first()
                av_item = GachaItem.objects.filter(name=profile.current_avatar).first()
                return render(request, "sns/edit_profile.html", {
                    "my_items": list(real_owned_titles),
                    "my_avatars": owned_items.filter(icon_query),
                    "current_rarity": current_item.rarity if current_item else "N",
                    "current_av_rarity": av_item.rarity if av_item else "N",
                    "owned_names": [n for n in NAMES_LIST if any(n in item.name for item in real_owned_titles)],
                    "owned_words": [w for w in WORDS_LIST if any(w in item.name for item in real_owned_titles)],
                    "username_error": username_error,
                    "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
                })
            return redirect("edit_profile")

        if "new_avatar" in request.POST:
            new_avatar = request.POST.get("new_avatar")
            if owned_items.filter(name=new_avatar).exists():
                profile.current_avatar = new_avatar
                profile.save(update_fields=["current_avatar"])
            return redirect("index")

        if "custom_name" in request.POST:
            c_name = request.POST.get("custom_name")
            c_word = request.POST.get("custom_word")
            order = request.POST.get("order")
            valid_names = [n for n in NAMES_LIST if any(n in item.name for item in real_owned_titles)]
            valid_words = [w for w in WORDS_LIST if any(w in item.name for item in real_owned_titles)]
            if c_name in valid_names and c_word in valid_words:
                full_title = f"{c_word}{c_name}" if order == "reverse" else f"{c_name}{c_word}"
                max_rarity_val = 1
                val_to_r = {1: "N", 2: "R", 3: "SR", 4: "SSR", 5: "UR", 6: "LR"}
                for item in real_owned_titles:
                    if c_name in item.name or c_word in item.name:
                        max_rarity_val = max(max_rarity_val, RARITY_ORDER.get(item.rarity, 1))
                new_item, created_item = GachaItem.objects.get_or_create(
                    name=full_title, defaults={"rarity": val_to_r[max_rarity_val]}
                )
                profile.items.add(new_item)
                profile.current_title = full_title
                profile.save(update_fields=["current_title"])
                return redirect("index")

    owned_names = [n for n in NAMES_LIST if any(n in item.name for item in real_owned_titles)]
    owned_words = [w for w in WORDS_LIST if any(w in item.name for item in real_owned_titles)]
    current_item = GachaItem.objects.filter(name=profile.current_title).first()
    av_item = GachaItem.objects.filter(name=profile.current_avatar).first()

    return render(request, "sns/edit_profile.html", {
        "my_items": list(real_owned_titles),
        "my_avatars": owned_items.filter(icon_query),
        "current_rarity": current_item.rarity if current_item else "N",
        "current_av_rarity": av_item.rarity if av_item else "N",
        "owned_names": owned_names,
        "owned_words": owned_words,
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })


@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    owned_items = profile.items.all().order_by("-rarity", "name")
    icon_query = Q(name__contains="【アイコン】") | Q(name__contains="アイコン") | Q(name__contains="繧｢繧､繧ｳ繝ｳ")
    real_owned_titles = owned_items.exclude(icon_query)

    def render_profile(username_error=None):
        current_item = GachaItem.objects.filter(name=profile.current_title).first()
        av_item = GachaItem.objects.filter(name=profile.current_avatar).first()
        owned_parts = owned_title_parts(real_owned_titles)
        title_rows = [
            {
                "item": item,
                "display_name": item_display_name(item),
                "sell_value": SELL_VALUES.get(item.rarity, 0),
                "can_sell": item.name != profile.current_title and not is_refined_item(item),
                "is_refined": is_refined_item(item),
            }
            for item in real_owned_titles
        ]
        avatar_rows = [
            {
                "item": item,
                "display_name": item_display_name(item),
                "sell_value": SELL_VALUES.get(item.rarity, 0),
                "can_sell": item.name != profile.current_avatar and not is_refined_item(item),
                "is_refined": is_refined_item(item),
            }
            for item in owned_items.filter(icon_query)
        ]
        return render(request, "sns/edit_profile.html", {
            "my_items": list(real_owned_titles),
            "my_avatars": owned_items.filter(icon_query),
            "title_rows": title_rows,
            "avatar_rows": avatar_rows,
            "buy_rows": [
                {"rarity": rarity, "cost": BUY_COSTS[rarity], "sell": SELL_VALUES[rarity]}
                for rarity in ["N", "R", "SR", "SSR", "UR", "LR"]
            ],
            "sell_values": SELL_VALUES,
            "rarity_labels": RARITY_LABELS,
            "points": profile.points,
            "exchange_points": profile.exchange_points,
            "title_words": owned_parts["words"],
            "title_names": owned_parts["names"],
            "title_nouns": owned_parts["nouns"],
            "shop_catalog": SHOP_CATALOG,
            "current_rarity": current_item.rarity if current_item else "N",
            "current_av_rarity": av_item.rarity if av_item else "N",
            "username_error": username_error,
            "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
        })

    if request.method == "POST":
        if "update_profile" in request.POST:
            requested_username = (request.POST.get("username") or "").strip()
            username_error = None
            if requested_username and requested_username != request.user.username:
                if User.objects.filter(username=requested_username).exclude(id=request.user.id).exists():
                    username_error = "このIDはすでに使われています。別のIDにしてください。"
                else:
                    request.user.username = requested_username
                    request.user.save(update_fields=["username"])

            profile.display_name = request.POST.get("display_name")
            profile.bio = request.POST.get("bio")
            profile.department = request.POST.get("department")
            profile.theme_color = request.POST.get("theme_color", "dark")
            profile.target_date = request.POST.get("target_date") or None
            profile.target_minutes = int(request.POST.get("target_minutes") or 0)
            if "icon" in request.FILES:
                profile.icon = file_to_base64(request.FILES["icon"])
            profile.save()
            if username_error:
                return render_profile(username_error)
            return redirect("edit_profile")

        if "new_avatar" in request.POST:
            new_avatar = request.POST.get("new_avatar")
            if owned_items.filter(name=new_avatar).exists():
                profile.current_avatar = new_avatar
                profile.save(update_fields=["current_avatar"])
            return redirect("edit_profile")

        if "equip_title" in request.POST:
            new_title = request.POST.get("equip_title")
            if real_owned_titles.filter(name=new_title).exists():
                profile.current_title = new_title
                profile.save(update_fields=["current_title"])
            return redirect("edit_profile")

        if "combine_titles" in request.POST:
            title_a = request.POST.get("title_a")
            title_b = request.POST.get("title_b")
            order = request.POST.get("order")
            item_a = real_owned_titles.filter(name=title_a).first()
            item_b = real_owned_titles.filter(name=title_b).first()
            if item_a and item_b and item_a.id != item_b.id:
                left, right = (item_display_name(item_b), item_display_name(item_a)) if order == "reverse" else (item_display_name(item_a), item_display_name(item_b))
                base_name = f"{left}{right}"
                full_title = f"精錬:{base_name[:95]}"
                max_rarity_val = max(RARITY_ORDER.get(item_a.rarity, 1), RARITY_ORDER.get(item_b.rarity, 1))
                new_item, created_item = GachaItem.objects.get_or_create(
                    name=full_title, defaults={"rarity": RARITY_BY_VALUE[max_rarity_val]}
                )
                profile.items.add(new_item)
                profile.current_title = full_title
                profile.save(update_fields=["current_title"])
            return redirect("edit_profile")

        if "refine_parts" in request.POST:
            word = (request.POST.get("title_word") or "").strip()[:30]
            noun = (request.POST.get("title_noun") or "").strip()[:30]
            name = (request.POST.get("title_name") or "").strip()[:30]
            order = request.POST.get("custom_order")
            owned_parts = owned_title_parts(real_owned_titles)
            valid_word = not word or word in owned_parts["words"]
            valid_noun = not noun or noun in owned_parts["nouns"]
            valid_name = not name or name in owned_parts["names"]
            if (word or noun or name) and valid_word and valid_noun and valid_name:
                if order == "name_first":
                    full_title = f"{name}{word}{noun}"
                elif order == "noun_first":
                    full_title = f"{noun}{word}{name}"
                else:
                    full_title = f"{word}{noun}{name}"
                rarity_value = max(
                    refined_part_rarity(word, real_owned_titles),
                    refined_part_rarity(noun, real_owned_titles),
                    refined_part_rarity(name, real_owned_titles),
                )
                new_item, created_item = GachaItem.objects.get_or_create(
                    name=f"精錬:{full_title[:47]}", defaults={"rarity": RARITY_BY_VALUE[rarity_value]}
                )
                profile.items.add(new_item)
                profile.current_title = new_item.name
                profile.save(update_fields=["current_title"])
            return redirect("edit_profile")

        if "sell_selected" in request.POST:
            sell_items(profile, profile.items.filter(id__in=request.POST.getlist("sell_items")))
            return redirect("edit_profile")

        if "bulk_sell" in request.POST:
            max_rarity = request.POST.get("bulk_sell")
            max_value = RARITY_ORDER.get(max_rarity, 0)
            targets = [
                item for item in profile.items.all()
                if RARITY_ORDER.get(item.rarity, 0) <= max_value
            ]
            sell_items(profile, targets)
            return redirect("edit_profile")

        if "buy_rarity" in request.POST:
            rarity = request.POST.get("buy_rarity")
            cost = BUY_COSTS.get(rarity)
            if cost and profile.exchange_points >= cost:
                profile.exchange_points -= cost
                item_type = request.POST.get("item_type", "title")
                selected_name = request.POST.get("shop_item_name", "")
                allowed_names = SHOP_CATALOG.get(item_type, {}).get(rarity, [])
                item_name = selected_name if selected_name in allowed_names else (allowed_names[0] if allowed_names else shop_item_name(rarity))
                item, created_item = GachaItem.objects.get_or_create(
                    name=item_name,
                    defaults={"rarity": rarity}
                )
                profile.items.add(item)
                profile.save(update_fields=["exchange_points"])
            return redirect("edit_profile")

    return render_profile()


def logout_view(request):
    session_id = request.session.get("login_session_id")
    if session_id and request.user.is_authenticated:
        now = timezone.now()
        UserLoginSession.objects.filter(
            id=session_id, user=request.user, logout_at__isnull=True
        ).update(logout_at=now, last_seen_at=now)
        request.session.pop("login_session_id", None)
    logout(request)
    return redirect("login")


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
    else:
        form = UserCreationForm()
    return render(request, "sns/signup.html", {"form": form})


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.liked_by.all():
        post.liked_by.remove(request.user)
    else:
        post.liked_by.add(request.user)
        if post.user != request.user:
            Notification.objects.create(recipient=post.user, sender=request.user, post=post, notification_type="like")
    return redirect("index")


@login_required
def user_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile, created = Profile.objects.get_or_create(user=target_user)
    active_tab = request.GET.get("tab", "posts")
    base_query = Post.objects.select_related("user", "user__profile").prefetch_related("liked_by", "comments")

    if active_tab == "likes":
        query_data = base_query.filter(liked_by=target_user).order_by("-created_at")
    elif active_tab == "followers":
        query_data = target_profile.followed_by.select_related("user").all()
    elif active_tab == "following":
        query_data = target_profile.follows.select_related("user").all()
    else:
        query_data = base_query.filter(user=target_user).order_by("-created_at")

    page_obj = Paginator(query_data, 10).get_page(request.GET.get("page"))
    if active_tab in ["posts", "likes"]:
        for post in page_obj:
            post.display_study_time = format_study_time(post.study_minutes)
            post.subject_color = subject_color(post.subject)

    target_posts = Post.objects.filter(user=target_user, study_minutes__gt=0)
    total_minutes = target_posts.aggregate(Sum("study_minutes"))["study_minutes__sum"] or 0
    month_start = timezone.localdate().replace(day=1)
    month_minutes = target_posts.filter(created_at__date__gte=month_start).aggregate(Sum("study_minutes"))[
        "study_minutes__sum"
    ] or 0
    subject_rows = build_subject_rows(target_posts)
    title_item = GachaItem.objects.filter(name=target_profile.current_title).first()
    av_item = GachaItem.objects.filter(name=target_profile.current_avatar).first()
    my_profile, created = Profile.objects.get_or_create(user=request.user)

    return render(request, "sns/user_profile.html", {
        "target_user": target_user,
        "target_profile": target_profile,
        "page_obj": page_obj,
        "active_tab": active_tab,
        "is_following": my_profile.follows.filter(id=target_profile.id).exists(),
        "target_title_rarity": title_item.rarity if title_item else "N",
        "target_av_rarity": av_item.rarity if av_item else "N",
        "followers_count": target_profile.followed_by.count(),
        "following_count": target_profile.follows.count(),
        "total_study_display": format_study_time(total_minutes),
        "month_study_display": format_study_time(month_minutes),
        "post_count": Post.objects.filter(user=target_user).count(),
        "subject_labels": json.dumps([row["subject"] for row in subject_rows]),
        "subject_data": json.dumps([row["total"] for row in subject_rows]),
        "subject_colors": json.dumps([row["color"] for row in subject_rows]),
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })


@login_required
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile, created = Profile.objects.get_or_create(user=target_user)
    my_profile, created = Profile.objects.get_or_create(user=request.user)
    if request.user != target_user:
        if my_profile.follows.filter(id=target_profile.id).exists():
            my_profile.follows.remove(target_profile)
        else:
            my_profile.follows.add(target_profile)
            Notification.objects.create(recipient=target_user, sender=request.user, notification_type="follow")
    return redirect("user_profile", username=username)


@login_required
def notifications_view(request):
    notifs = Notification.objects.select_related("sender", "sender__profile").filter(
        recipient=request.user
    ).order_by("-created_at")[:30]
    for notif in notifs:
        notif.sender_label = account_label(notif.sender)
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, "sns/notifications.html", {"notifications": notifs, "unread_count": 0})


@login_required
def analytics_view(request):
    start, end = selected_date_range(request, default_days=30)
    user_posts = Post.objects.filter(user=request.user, study_minutes__gt=0, created_at__date__range=(start, end))
    subject_rows = build_subject_rows(user_posts)
    total_minutes = user_posts.aggregate(Sum("study_minutes"))["study_minutes__sum"] or 0

    day_rows = user_posts.annotate(day=TruncDate("created_at")).values("day").annotate(total=Sum("study_minutes"))
    totals_by_day = {row["day"]: row["total"] or 0 for row in day_rows}
    days = (end - start).days + 1
    bar_labels = [(start + timedelta(days=i)).strftime("%m/%d") for i in range(days)]
    bar_data = [totals_by_day.get(start + timedelta(days=i), 0) for i in range(days)]

    ranking = build_ranking(start, end, limit=5)

    return render(request, "sns/analytics.html", {
        "start": start,
        "end": end,
        "pie_labels": json.dumps([row["subject"] for row in subject_rows]),
        "pie_data": json.dumps([row["total"] for row in subject_rows]),
        "pie_colors": json.dumps([row["color"] for row in subject_rows]),
        "bar_labels": json.dumps(bar_labels),
        "bar_data": json.dumps(bar_data),
        "subject_list": subject_rows,
        "ranking": ranking,
        "total_all_time_display": format_study_time(total_minutes),
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })


def build_ranking(start, end, limit=30):
    rows = (
        Post.objects.filter(study_minutes__gt=0, created_at__date__range=(start, end))
        .values("user")
        .annotate(total=Sum("study_minutes"), posts=Count("id"))
        .order_by("-total")[:limit]
    )
    users = {user.id: user for user in User.objects.select_related("profile").filter(id__in=[row["user"] for row in rows])}
    ranking = []
    for index, row in enumerate(rows, start=1):
        user = users.get(row["user"])
        if not user:
            continue
        ranking.append({
            "rank": index,
            "user": user,
            "label": account_label(user),
            "display_time": format_study_time(row["total"]),
            "total": row["total"],
            "posts": row["posts"],
        })
    return ranking


@login_required
def rankings_view(request):
    start, end = selected_date_range(request, default_days=7)
    ranking = build_ranking(start, end, limit=50)
    return render(request, "sns/rankings.html", {
        "start": start,
        "end": end,
        "ranking": ranking,
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })


@login_required
@user_passes_test(is_site_admin)
def admin_login_activity(request):
    active_cutoff = timezone.now() - timedelta(minutes=15)
    sessions = UserLoginSession.objects.select_related("user").order_by("-login_at")[:100]
    active_count = 0
    for session in sessions:
        session.is_active_now = session.logout_at is None and session.last_seen_at >= active_cutoff
        if session.is_active_now:
            active_count += 1
    return render(request, "sns/admin_login_activity.html", {
        "sessions": sessions,
        "active_count": active_count,
        "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })
