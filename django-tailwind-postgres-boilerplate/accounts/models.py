from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extends the built-in User with a role flag.

    is_instructor=False -> student (can enroll in / view courses)
    is_instructor=True  -> instructor (gets access to the instructor dashboard
                            and can create/manage their own courses)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    is_instructor = models.BooleanField(default=False)
    bio = models.TextField(blank=True)

    def __str__(self):
        role = "Instructor" if self.is_instructor else "Student"
        return f"{self.user.username} ({role})"
