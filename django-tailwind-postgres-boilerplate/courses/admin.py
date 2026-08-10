from django.contrib import admin

from .models import Category, Course, Enrollment, Lesson, LessonProgress, Module


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "category", "price", "is_published", "created_at")
    list_filter = ("is_published", "category")
    search_fields = ("title", "instructor__username")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "is_preview")
    list_filter = ("is_preview",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "amount_paid", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "course__title")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed_at")
    search_fields = ("user__username", "lesson__title")
