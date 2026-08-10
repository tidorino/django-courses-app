from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses"
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses_taught"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cover_image = models.ImageField(upload_to="course_covers/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            i = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:course_detail", args=[self.slug])

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    def progress_percent(self, user):
        """Percentage of this course's lessons the given user has completed."""
        if not user.is_authenticated:
            return 0
        total = self.lesson_count
        if total == 0:
            return 0
        completed = LessonProgress.objects.filter(
            user=user, lesson__module__course=self
        ).count()
        return round((completed / total) * 100)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    text_content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube link or direct video file URL")
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(
        default=False, help_text="Free preview — visible without enrolling"
    )

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            i = 1
            while Lesson.objects.filter(module=self.module, slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def course(self):
        return self.module.course

    def __str__(self):
        return f"{self.module.course.title} — {self.title}"


class Enrollment(models.Model):
    """Tracks who has access to which course.

    No real payment gateway is wired up yet — `enroll` creates this record
    with status="completed" directly. This is the natural place to plug in
    Stripe (or similar) later: create as "pending", redirect to checkout,
    then flip to "completed" via a webhook/return view.
    """
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("refunded", "Refunded"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} → {self.course.title} ({self.status})"


class LessonProgress(models.Model):
    """A row exists only for lessons the user has marked complete."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user.username} completed {self.lesson.title}"
