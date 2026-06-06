from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='tracker:landing'), name='logout'),
    path('', include('tracker.urls')),
]
