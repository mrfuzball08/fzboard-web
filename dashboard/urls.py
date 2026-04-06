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

    # Dataset management
    path('datasets/', views.dataset_list, name='dataset_list'),
    path('datasets/crear/', views.dataset_create, name='dataset_create'),
    path('datasets/<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('datasets/<int:pk>/upload/', views.dataset_upload, name='dataset_upload'),
    path('datasets/<int:pk>/upload/mapping/', views.dataset_upload_mapping, name='dataset_upload_mapping'),
    path('datasets/<int:pk>/imports/<int:import_pk>/', views.dataset_import_detail, name='dataset_import_detail'),
    path('datasets/<int:pk>/eliminar/', views.dataset_delete, name='dataset_delete'),

    # Report management
    path('reports/', views.report_list, name='report_list'),
    path('reports/crear/', views.report_create, name='report_create'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/builder/', views.report_builder, name='report_builder'),
    path('reports/<int:pk>/eliminar/', views.report_delete, name='report_delete'),

    # Report API (used by Svelte builder)
    path('reports/<int:pk>/api/widgets/', views.report_widget_api, name='report_widget_api'),
    path('reports/<int:pk>/api/widgets/<int:widget_pk>/', views.report_widget_api, name='report_widget_api_detail'),
    path('reports/<int:pk>/api/filters/', views.report_filter_api, name='report_filter_api'),
    path('reports/<int:pk>/api/filters/<int:filter_pk>/', views.report_filter_api, name='report_filter_api_detail'),
    path('reports/<int:pk>/api/preview/', views.report_widget_preview, name='report_widget_preview'),
]
