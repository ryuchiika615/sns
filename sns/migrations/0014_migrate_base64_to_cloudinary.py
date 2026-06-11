import base64

from django.core.files.base import ContentFile
from django.db import migrations


def migrate_base64_images(apps, schema_editor):
    Post = apps.get_model("sns", "Post")
    Profile = apps.get_model("sns", "Profile")
    ext_map = {
        "jpeg": "jpg",
        "png": "png",
        "gif": "gif",
        "webp": "webp",
        "svg+xml": "svg",
    }

    for post in Post.objects.all():
        if (
            post.image
            and isinstance(post.image, str)
            and post.image.startswith("data:")
        ):
            try:
                format_str, imgstr = post.image.split(";base64,")
                ext = format_str.split("/")[-1]
                ext = ext_map.get(ext, "jpg")
                data = ContentFile(
                    base64.b64decode(imgstr), name=f"post_{post.id}.{ext}"
                )
                post.image_file = data
                post.save(update_fields=["image_file"])
            except Exception:
                pass

    for profile in Profile.objects.all():
        if (
            profile.icon
            and isinstance(profile.icon, str)
            and profile.icon.startswith("data:")
        ):
            try:
                format_str, imgstr = profile.icon.split(";base64,")
                ext = format_str.split("/")[-1]
                ext = ext_map.get(ext, "jpg")
                data = ContentFile(
                    base64.b64decode(imgstr), name=f"icon_{profile.id}.{ext}"
                )
                profile.icon_file = data
                profile.save(update_fields=["icon_file"])
            except Exception:
                pass


class Migration(migrations.Migration):
    dependencies = [
        ("sns", "0013_post_image_file_profile_icon_file"),
    ]

    operations = [
        migrations.RunPython(
            migrate_base64_images, reverse_code=migrations.RunPython.noop
        ),
    ]
