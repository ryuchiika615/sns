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
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import Comment, GachaItem, Notification, Post, Profile, UserLoginSession


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

SUBJECT_COLORS = [
    "#1877f2", "#ff6b6b", "#20c997", "#f59f00", "#845ef7", "#12b886",
    "#e64980", "#15aabf", "#fd7e14", "#5c7cfa", "#82c91e", "#be4bdb",
]
RARITY_ORDER = {"N": 1, "R": 2, "SR": 3, "SSR": 4, "UR": 5, "LR": 6}


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
    dt = timezone.make_aware(datetime.combine(study_date, time(hour=12)))
    Post.objects.filter(id=post.id).update(created_at=dt)
    post.created_at = dt


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
        else:
            Profile.objects.get_or_create(user=post.user)
            post.current_rarity = "N"
            post.avatar_rarity = "N"
        post.display_study_time = format_study_time(post.study_minutes)
        post.subject_color = subject_color(post.subject)
        post.author_label = account_label(post.user)
        diff = now - post.created_at
        if diff.days > 0:
            post.formatted_time = post.created_at.strftime("%m/%d %H:%M")
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

    if request.method == "POST":
        pull_count = 10 if "gacha_10" in request.POST else 1
        cost = pull_count * 10
        if profile.points >= cost:
            profile.points -= cost
            for _ in range(pull_count):
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

                if rarity in ["LR", "UR"]:
                    generated_name = f"{random.choice(LEGENDARY_PREFIXES)}{random.choice(LEGENDARY_NOUNS)}"
                elif random.random() < 0.25:
                    generated_name = f"{random.choice(CUTE_PREFIXES)}{random.choice(CUTE_NOUNS)}"
                elif random.random() < 0.45:
                    generated_name = f"【アイコン】{random.choice(ANIMAL_PREFIXES)}{random.choice(ANIMAL_NOUNS)}"
                elif random.choice([True, False]):
                    generated_name = f"【アイコン】{random.choice(AVATAR_PREFIXES)}{random.choice(AVATAR_NOUNS)}"
                elif random.choice([True, False]):
                    generated_name = f"{random.choice(NAMES_LIST)}{random.choice(WORDS_LIST)}"
                else:
                    generated_name = f"{random.choice(WORDS_LIST)}{random.choice(NAMES_LIST)}"

                result_item, created_item = GachaItem.objects.get_or_create(
                    name=generated_name, defaults={"rarity": rarity}
                )
                result_items.append(result_item)
                profile.items.add(result_item)
            profile.save(update_fields=["points"])
        else:
            error = "ポイントが足りません。勉強してポイントを貯めよう。"

    return render(request, "sns/gacha.html", {
        "result_items": result_items,
        "points": profile.points,
        "error": error,
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
