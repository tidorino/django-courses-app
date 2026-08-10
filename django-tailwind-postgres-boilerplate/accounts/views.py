from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm
from .models import Profile


def signup(request):
    if request.user.is_authenticated:
        return redirect("courses:course_list")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                is_instructor=(form.cleaned_data["role"] == "instructor"),
            )
            login(request, user)
            return redirect("courses:course_list")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})
