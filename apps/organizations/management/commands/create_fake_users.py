import random
import re

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.db import IntegrityError

from faker import Faker

user_model = apps.get_model(settings.AUTH_USER_MODEL)
fake = Faker()
used_usernames = []
used_emails = []


def get_username(first_name, last_name):
    patterns = (
        "{last_name}.{first_name}",
        "{first_name}.{last_name}",
        "{first_name}##",
        "?{last_name}",
    )
    pattern = fake.random_element(patterns)
    username = pattern.format(first_name=first_name, last_name=last_name)
    username = re.sub(r"[\W]+", "", fake.bothify(username).lower())
    if username in used_usernames:
        get_username(first_name, last_name)
    used_usernames.append(username)
    return username


def get_email(username):
    domain_func_name = fake.random_element(["domain_name", "free_email_domain"])
    email = f"{username}@{getattr(fake, domain_func_name)()}"
    if email in used_emails:
        get_email(username)
    used_emails.append(username)
    return email


def get_person():
    gender = random.choice(["male", "female"])  # noqa: S311
    name = fake.name_male() if gender == "male" else fake.name_female()
    name_parts = name.split(" ")
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])
    username = get_username(first_name, last_name)
    return {
        "gender": gender,
        "username": username,
        "email": get_email(username),
        "first_name": first_name,
        "last_name": last_name,
    }


def create_person():
    person = get_person()
    person.pop("gender")
    username = person.pop("username")
    email = person.pop("email")
    try:
        user_model.objects.create_user(username=username, email=email, **person)
    except IntegrityError:
        create_person()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--number", type=int, default=1000, help="Number of users to create.")

    def handle(self, **options):
        for _i in range(options["number"]):
            create_person()
