from django import forms

from .models import Course, Lesson, Module


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "category", "price", "cover_image", "is_published"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["title", "order"]


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "text_content", "video_url", "order", "is_preview"]
        widgets = {"text_content": forms.Textarea(attrs={"rows": 8})}
