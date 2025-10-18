from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View


class RegisterView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "users/register.html", {"form": UserCreationForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
        return render(request, "users/register.html", {"form": form})


class LoginView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "users/login.html", {"form": AuthenticationForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("image_list")
        return render(request, "users/login.html", {"form": form})


class LogoutView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect("login")
