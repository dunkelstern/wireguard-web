from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template import loader
from django.urls import reverse
from django.utils.http import urlencode


User = get_user_model()


def send_reset_mail(request, user: User, template: str, subject: str):
    generator = PasswordResetTokenGenerator()
    template = loader.get_template(template)
    link = (
        settings.BASE_URL
        + reverse("reset-password")
        + "?"
        + urlencode({"token": generator.make_token(user), "email": user.email})
    )

    rendered = template.render({"server": settings.BASE_URL, "link": link, "name": user.name})
    send_mail(subject, rendered, None, [user.email], fail_silently=True)
