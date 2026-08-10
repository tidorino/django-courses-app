from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("my-courses/", views.my_courses, name="my_courses"),

    # Instructor dashboard
    path("instructor/", views.instructor_dashboard, name="instructor_dashboard"),
    path("instructor/courses/new/", views.course_create, name="instructor_course_create"),
    path("instructor/courses/<slug:slug>/edit/", views.course_edit, name="instructor_course_edit"),
    path("instructor/courses/<slug:slug>/modules/new/", views.module_create, name="instructor_module_create"),
    path("instructor/courses/<slug:slug>/modules/<int:module_id>/delete/", views.module_delete, name="instructor_module_delete"),
    path("instructor/courses/<slug:slug>/modules/<int:module_id>/lessons/new/", views.lesson_create, name="instructor_lesson_create"),
    path("instructor/courses/<slug:slug>/lessons/<int:lesson_id>/edit/", views.lesson_edit, name="instructor_lesson_edit"),
    path("instructor/courses/<slug:slug>/lessons/<int:lesson_id>/delete/", views.lesson_delete, name="instructor_lesson_delete"),

    # Public course pages (kept below instructor/ and my-courses/ so slugs don't clash)
    path("<slug:slug>/", views.course_detail, name="course_detail"),
    path("<slug:slug>/enroll/", views.enroll, name="enroll"),
    path("<slug:course_slug>/lessons/<slug:lesson_slug>/", views.lesson_detail, name="lesson_detail"),
    path("<slug:course_slug>/lessons/<slug:lesson_slug>/toggle-complete/", views.toggle_lesson_complete, name="toggle_lesson_complete"),
]
