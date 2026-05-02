import io
import json
import logging

from django.apps import apps
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ninja import File, Form, Query, Router, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.pagination import paginate
from PIL import Image

from apps.accounts.schemas import AvatarOut, ImpersonateUserOut, UserOut, UserPatchIn
from apps.base.ninja_pagination import make_pagination
from apps.base.permissions import require_authenticated

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
THUMBNAIL_SIZE = 256


def get_user_model():
    return apps.get_model(settings.AUTH_USER_MODEL)


users_router = Router(tags=["users"])
avatar_router = Router(tags=["avatar"])


def _users_qs(request):
    User = get_user_model()
    filter_kwargs = {"is_active": True}
    if request.org.id is None:
        filter_kwargs["pk"] = request.user.pk
    else:
        filter_kwargs["organizationmember__organization"] = request.org.pk
    return (
        User.objects.filter(**filter_kwargs)
        .only("id", "username", "first_name", "last_name", "timezone")
        .order_by("first_name")
    )


@users_router.get("/", response=list[UserOut])
@paginate(make_pagination(default_page_size=50))
def list_users(request, q: str | None = Query(None)):
    require_authenticated(request)
    qs = _users_qs(request)
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
    return qs


@users_router.get("/impersonate-search/", response=list[ImpersonateUserOut])
def impersonate_search(request, q: str = Query("")):
    require_authenticated(request)
    if not request.user.is_staff:
        raise HttpError(403, "Admin permission required.")
    User = get_user_model()
    qs = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    q = q.strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q)
        )
    qs = qs.order_by("first_name", "last_name")[:20]
    return [
        {
            "id": u.pk,
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "full_name": u.get_full_name(),
            "avatar_url": u.avatar_url,
        }
        for u in qs
    ]


@users_router.get("/{user_id}/", response=UserOut)
def get_user(request, user_id: int):
    require_authenticated(request)
    return get_object_or_404(_users_qs(request), pk=user_id)


@users_router.patch("/{user_id}/", response=UserOut)
def patch_user(request, user_id: int, payload: UserPatchIn):
    require_authenticated(request)
    user = get_object_or_404(_users_qs(request), pk=user_id)
    if user != request.user:
        raise HttpError(403, "You can only update your own profile.")
    old_tz = user.timezone
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    user.full_clean()
    user.save()
    if user.timezone != old_tz:
        logger.info("User %s timezone changed from %s to %s", user.pk, old_tz, user.timezone)
    return user


@avatar_router.post("/", response=AvatarOut)
def upload_avatar(
    request,
    image: UploadedFile = File(...),
    crop_data: str = Form("{}"),
):
    require_authenticated(request)
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HttpError(400, "Unsupported image type. Use JPEG, PNG, or WebP.")
    if image.size > MAX_UPLOAD_SIZE:
        raise HttpError(400, "Image must be under 10 MB.")

    try:
        crop = json.loads(crop_data or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise HttpError(400, "Invalid crop_data: must be JSON.") from exc
    if not isinstance(crop, dict):
        raise HttpError(400, "Invalid crop_data: must be a JSON object.")

    crop_box = None
    if crop.get("width") and crop.get("height"):
        try:
            left = int(crop["left"])
            top = int(crop["top"])
            width = int(crop["width"])
            height = int(crop["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HttpError(400, "Invalid crop_data: left/top/width/height must be numbers.") from exc
        crop_box = (left, top, left + width, top + height)

    image.seek(0)
    try:
        img = Image.open(image).convert("RGB")
    except Exception as exc:
        raise HttpError(400, "Could not decode the uploaded image.") from exc
    if crop_box is not None:
        img = img.crop(crop_box)
    img = img.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)
    thumb_io = io.BytesIO()
    img.save(thumb_io, format="JPEG", quality=90)
    thumb_file = InMemoryUploadedFile(thumb_io, None, "thumbnail.jpg", "image/jpeg", thumb_io.tell(), None)

    user = request.user
    # Capture the previous storage paths before the field assignments below
    # overwrite them; we only delete them after the model row commits, so a
    # mid-upload failure leaves the prior avatar intact.
    old_original = user.avatar_original.name if user.avatar_original else None
    old_thumb = user.avatar_thumbnail.name if user.avatar_thumbnail else None
    old_original_storage = user.avatar_original.storage if user.avatar_original else None
    old_thumb_storage = user.avatar_thumbnail.storage if user.avatar_thumbnail else None

    image.seek(0)
    user.avatar_original.save(image.name, image, save=False)
    user.avatar_thumbnail.save("thumbnail.jpg", thumb_file, save=False)
    user.avatar_crop_data = crop
    user.save(update_fields=["avatar_original", "avatar_thumbnail", "avatar_crop_data"])

    if old_original and old_original != user.avatar_original.name:
        old_original_storage.delete(old_original)
    if old_thumb and old_thumb != user.avatar_thumbnail.name:
        old_thumb_storage.delete(old_thumb)

    return {"avatar_url": user.avatar_url}


@avatar_router.delete("/", response={204: None})
def delete_avatar(request):
    require_authenticated(request)
    user = request.user
    if user.avatar_original:
        user.avatar_original.delete(save=False)
    if user.avatar_thumbnail:
        user.avatar_thumbnail.delete(save=False)
    user.avatar_crop_data = None
    user.save(update_fields=["avatar_original", "avatar_thumbnail", "avatar_crop_data"])
    return Status(204, None)
