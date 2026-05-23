import binascii
import os
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..base.mixins import TimeStampModelMixin
from ..base.utils.email import send_email
from .managers import OrganizationInviteQuerySet, OrganizationMemberQuerySet, OrganizationQuerySet


def get_user_model():
    return apps.get_model(settings.AUTH_USER_MODEL)


class Organization(TimeStampModelMixin):
    name = models.CharField(max_length=75, verbose_name=_("display name"))
    slug = models.SlugField(
        max_length=40,
        unique=True,
        verbose_name=_("account name"),
        help_text=_("The account name is like a username and ideally should be lower case and short."),
        error_messages={"invalid": _("Enter a valid name consisting of letters, numbers, underscores or hyphens.")},
    )
    billing_email = models.EmailField(null=True, blank=True, help_text="The email address that receipts are sent.")
    objects = OrganizationQuerySet.as_manager()

    def __str__(self):
        """Return the organization name."""
        return self.name

    def clean(self):
        if get_user_model().objects.filter(username=self.slug).exists() is True:
            raise ValidationError({"slug": [_("Account name is already taken.")]})

    def is_member(self, user):
        return OrganizationMember.objects.filter(organization=self, user=user).exists()

    def is_owner(self, user):
        return OrganizationMember.objects.filter(organization=self, user=user, is_owner=True).exists()

    @property
    def members(self):
        return get_user_model().objects.filter(pk__in=self.organizationmember_set.values_list("user_id", flat=True))

    @property
    def regular_members(self):
        return get_user_model().objects.filter(
            pk__in=self.organizationmember_set.filter(is_owner=False).values_list("user_id", flat=True)
        )

    @property
    def owners(self):
        return get_user_model().objects.filter(
            pk__in=self.organizationmember_set.filter(is_owner=True).values_list("user_id", flat=True)
        )


class OrganizationRoleMixin(models.Model):
    is_owner = models.BooleanField(default=False, verbose_name=_("owner"))

    class Meta:
        abstract = True


class OrganizationMember(OrganizationRoleMixin, TimeStampModelMixin):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, verbose_name=_("primary"))
    objects = OrganizationMemberQuerySet.as_manager()

    class Meta:
        unique_together = ("organization", "user")

    def unique_error_message(self, model_class, unique_check):
        if model_class is type(self) and unique_check == ("organization", "user"):
            return _("This member already exists in this organization.")
        else:
            return super().unique_error_message(model_class, unique_check)

    def send_removal_email(self, sending_user):
        if not self.user.email:
            return
        context = {
            "user": self.user,
            "organization": self.organization,
        }
        send_email(
            sending_user=sending_user,
            recipients=[self.user],
            subject=f"You've been removed from the {self.organization} organization",
            base_template_name="organizations/emails/removed",
            context=context,
        )

    def send_owner_email(self, sending_user):
        send_email(
            sending_user=sending_user,
            recipients=[self.user],
            subject=f"You've been made an owner of the {self.organization} organization",
            base_template_name="organizations/emails/owner",
            context={
                "user": self.user,
                "organization": self.organization,
            },
        )


class OrganizationInvite(OrganizationRoleMixin, TimeStampModelMixin):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.CASCADE)
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="invitees", null=True, blank=True, on_delete=models.CASCADE
    )
    invitee_email = models.EmailField(null=True, blank=True)
    key = models.CharField(max_length=32, editable=False)
    objects = OrganizationInviteQuerySet.as_manager()

    expired_in_days = 7

    @property
    def is_expired(self):
        return (timezone.now() - self.created) > timedelta(days=self.expired_in_days)

    @property
    def invitee_first_name(self):
        if self.invitee is not None:
            return self.invitee.first_name
        else:
            return self.invitee_email

    @property
    def accept_invite_url(self):
        return reverse("accept_invite", args=[self.key])

    def clean(self):
        if self.invitee and not self.invitee_email:
            if not self.invitee.email:
                raise ValidationError(_("The invitee user is missing their email address."))
            else:
                # Set the invitee_email, so there is a record of what email was used,
                # in case they change their email address.
                self.invitee_email = self.invitee.email

        if not self.invitee and not self.invitee_email:
            raise ValidationError(_("Provide either an invitee or an email address."))

        if self.invitee and self.organization.is_member(self.invitee) is True:
            raise ValidationError(_(f'User "{self.invitee}" is already a member of this organization.'))

        # For some reason `unique_together = ('organization', 'sender', 'invitee', 'invitee_email')` didn't work so in
        # the meta class, so do it manually
        if (
            OrganizationInvite.objects.filter(
                organization=self.organization,
                sender=self.sender,
                invitee=self.invitee,
                invitee_email=self.invitee_email,
            ).exists()
            is True
        ):
            if self.invitee is not None:
                raise ValidationError(
                    _(
                        "There is already a pending invitation for the user,"
                        f" {self.invitee.get_full_name()} ({self.invitee.username})."
                    )
                )
            else:
                raise ValidationError(
                    _(f'There is already a pending invitation for the email address, "{self.invitee_email}".')
                )

    def save(self, **kwargs):
        self.full_clean()
        if not self.key:
            self.key = binascii.hexlify(os.urandom(20)).decode()[:32]
        super().save(**kwargs)

    def _send_email(self, subject: str, template_name: str, context: dict):
        context = {"site_url": settings.SITE_URL, **context}
        recipient = self.invitee.email if self.invitee else self.invitee_email
        send_email(
            sending_user=self.sender,
            recipients=[recipient],
            subject=subject,
            base_template_name=f"organizations/emails/{template_name}",
            context=context,
        )

    def send_invite(self):
        self._send_email(
            subject=f"Invite from {self.sender.get_full_name()}",
            template_name="invitation",
            context={
                "invite": self,
                "action_url": f"{settings.SITE_URL}{self.accept_invite_url}",
                "num_days": self.expired_in_days,
            },
        )

    def send_cancellation(self):
        self._send_email(
            subject=f"Your invitation to {self.organization} has been canceled",
            template_name="cancel_invitation",
            context={"invite": self},
        )
