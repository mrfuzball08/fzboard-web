from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Template management
    path('formatos/', views.template_list, name='template_list'),
    path('formatos/crear/', views.template_create, name='template_create'),
    path('formatos/<int:pk>/', views.template_detail, name='template_detail'),
    path('formatos/<int:pk>/eliminar/', views.template_delete, name='template_delete'),
    path('formatos/<int:pk>/descargar/', views.template_download_csv, name='template_download_csv'),
]
