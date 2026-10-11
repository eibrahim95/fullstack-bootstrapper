from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html", {"title": "__TITLE__"})
