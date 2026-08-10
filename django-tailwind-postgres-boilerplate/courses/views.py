from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import instructor_required
from .forms import CourseForm, LessonForm, ModuleForm
from .models import Course, Enrollment, Lesson, LessonProgress, Module


# ---------------------------------------------------------------------------
# Public / student-facing views
# ---------------------------------------------------------------------------

def course_list(request):
    courses = Course.objects.filter(is_published=True).select_related("instructor", "category")
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("instructor", "category").prefetch_related("modules__lessons"),
        slug=slug,
    )

    is_enrolled = False
    is_owner = False
    completed_lesson_ids = set()
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            user=request.user, course=course, status="completed"
        ).exists()
        is_owner = course.instructor_id == request.user.id
        completed_lesson_ids = set(
            LessonProgress.objects.filter(
                user=request.user, lesson__module__course=course
            ).values_list("lesson_id", flat=True)
        )

    if not course.is_published and not is_owner:
        raise PermissionDenied("This course isn't published yet.")

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "is_enrolled": is_enrolled,
            "is_owner": is_owner,
            "completed_lesson_ids": completed_lesson_ids,
            "progress_percent": course.progress_percent(request.user),
        },
    )


@login_required
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)

    if request.method != "POST":
        return redirect("courses:course_detail", slug=slug)

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={"amount_paid": course.price, "status": "completed"},
    )

    if created:
        messages.success(
            request,
            f"You're enrolled in \"{course.title}\"! "
            f"(No real payment was charged — this is a placeholder for a future payment gateway.)",
        )
    else:
        messages.info(request, "You're already enrolled in this course.")

    return redirect("courses:course_detail", slug=slug)


@login_required
def lesson_detail(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, module__course=course)

    is_owner = course.instructor_id == request.user.id
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=course, status="completed"
    ).exists()

    if not (lesson.is_preview or is_enrolled or is_owner):
        messages.warning(request, "Enroll in this course to access this lesson.")
        return redirect("courses:course_detail", slug=course_slug)

    modules = course.modules.prefetch_related("lessons")

    # Flatten lessons across all modules, in order, to find prev/next and completion state
    all_lessons = [l for m in modules for l in m.lessons.all()]
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            user=request.user, lesson__in=all_lessons
        ).values_list("lesson_id", flat=True)
    )
    is_completed = lesson.id in completed_lesson_ids

    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson.id), None)
    next_lesson = (
        all_lessons[current_index + 1] if current_index is not None and current_index + 1 < len(all_lessons) else None
    )
    previous_lesson = (
        all_lessons[current_index - 1] if current_index is not None and current_index > 0 else None
    )

    total = len(all_lessons)
    progress_percent = round((len(completed_lesson_ids) / total) * 100) if total else 0

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "course": course,
            "lesson": lesson,
            "modules": modules,
            "is_enrolled": is_enrolled,
            "is_completed": is_completed,
            "completed_lesson_ids": completed_lesson_ids,
            "next_lesson": next_lesson,
            "previous_lesson": previous_lesson,
            "progress_percent": progress_percent,
        },
    )


@login_required
def toggle_lesson_complete(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, module__course=course)

    is_owner = course.instructor_id == request.user.id
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=course, status="completed"
    ).exists()

    if not (is_enrolled or is_owner):
        raise PermissionDenied("Enroll in this course to track progress.")

    if request.method == "POST":
        progress, created = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        if not created:
            progress.delete()

    return redirect("courses:lesson_detail", course_slug=course_slug, lesson_slug=lesson_slug)


@login_required
def my_courses(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user, status="completed")
        .select_related("course")
    )
    for enrollment in enrollments:
        enrollment.progress_percent = enrollment.course.progress_percent(request.user)
    return render(request, "courses/my_courses.html", {"enrollments": enrollments})


# ---------------------------------------------------------------------------
# Instructor dashboard
# ---------------------------------------------------------------------------

@instructor_required
def instructor_dashboard(request):
    courses = Course.objects.filter(instructor=request.user).prefetch_related("modules__lessons")
    return render(request, "courses/instructor/dashboard.html", {"courses": courses})


@instructor_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, "Course created. Now add some modules and lessons.")
            return redirect("courses:instructor_course_edit", slug=course.slug)
    else:
        form = CourseForm()
    return render(request, "courses/instructor/course_form.html", {"form": form, "course": None})


def _get_owned_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor_id != request.user.id:
        raise PermissionDenied("You don't manage this course.")
    return course


@instructor_required
def course_edit(request, slug):
    course = _get_owned_course(request, slug)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated.")
            return redirect("courses:instructor_course_edit", slug=course.slug)
    else:
        form = CourseForm(instance=course)
    modules = course.modules.prefetch_related("lessons")
    return render(
        request,
        "courses/instructor/course_form.html",
        {"form": form, "course": course, "modules": modules},
    )


@instructor_required
def module_create(request, slug):
    course = _get_owned_course(request, slug)
    if request.method == "POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, "Module added.")
            return redirect("courses:instructor_course_edit", slug=course.slug)
    else:
        form = ModuleForm()
    return render(
        request, "courses/instructor/module_form.html", {"form": form, "course": course}
    )


@instructor_required
def module_delete(request, slug, module_id):
    course = _get_owned_course(request, slug)
    module = get_object_or_404(Module, pk=module_id, course=course)
    if request.method == "POST":
        module.delete()
        messages.success(request, "Module deleted.")
    return redirect("courses:instructor_course_edit", slug=course.slug)


@instructor_required
def lesson_create(request, slug, module_id):
    course = _get_owned_course(request, slug)
    module = get_object_or_404(Module, pk=module_id, course=course)
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            messages.success(request, "Lesson added.")
            return redirect("courses:instructor_course_edit", slug=course.slug)
    else:
        form = LessonForm()
    return render(
        request,
        "courses/instructor/lesson_form.html",
        {"form": form, "course": course, "module": module, "lesson": None},
    )


@instructor_required
def lesson_edit(request, slug, lesson_id):
    course = _get_owned_course(request, slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated.")
            return redirect("courses:instructor_course_edit", slug=course.slug)
    else:
        form = LessonForm(instance=lesson)
    return render(
        request,
        "courses/instructor/lesson_form.html",
        {"form": form, "course": course, "module": lesson.module, "lesson": lesson},
    )


@instructor_required
def lesson_delete(request, slug, lesson_id):
    course = _get_owned_course(request, slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module__course=course)
    if request.method == "POST":
        lesson.delete()
        messages.success(request, "Lesson deleted.")
    return redirect("courses:instructor_course_edit", slug=course.slug)
