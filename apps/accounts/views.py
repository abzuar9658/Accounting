from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PersonForm
from .models import Person


def _is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=settings.ROLE_ADMIN).exists()
    )


@login_required
def person_list(request):
    people = Person.objects.select_related("user").order_by("-is_active", "name")
    return render(request, "accounts/people_list.html", {"people": people})


@login_required
@user_passes_test(_is_admin)
def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, f"Added {person.name}.")
            return redirect("accounts:person_list")
    else:
        form = PersonForm()
    return render(request, "accounts/person_form.html", {"form": form})


@login_required
@user_passes_test(_is_admin)
def person_edit(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {person.name}.")
            return redirect("accounts:person_list")
    else:
        form = PersonForm(instance=person)
    return render(request, "accounts/person_form.html", {"form": form, "person": person})
