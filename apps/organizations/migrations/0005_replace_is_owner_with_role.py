from django.db import migrations, models

MODELS = ("OrganizationMember", "OrganizationInvite")


def is_owner_to_role(apps, schema_editor):
    for name in MODELS:
        model = apps.get_model("organizations", name)
        model.objects.filter(is_owner=True).update(role="owner")
        model.objects.filter(is_owner=False).update(role="member")


def role_to_is_owner(apps, schema_editor):
    # Any role but owner becomes a plain member, which is all the boolean can say.
    for name in MODELS:
        model = apps.get_model("organizations", name)
        model.objects.filter(role="owner").update(is_owner=True)
        model.objects.exclude(role="owner").update(is_owner=False)


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0004_add_is_primary_to_organizationmember"),
    ]

    operations = [
        *(
            migrations.AddField(
                model_name=name.lower(),
                name="role",
                field=models.CharField(
                    choices=[("owner", "owner"), ("member", "member")],
                    default="member",
                    max_length=20,
                    verbose_name="role",
                ),
            )
            for name in MODELS
        ),
        migrations.RunPython(is_owner_to_role, role_to_is_owner),
        *(migrations.RemoveField(model_name=name.lower(), name="is_owner") for name in MODELS),
    ]
