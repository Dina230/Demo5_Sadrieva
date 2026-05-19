from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-request/', views.create_request, name='create_request'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('', views.login_view),
]