from django.urls import path
from .views import dashboard_view, download_csv_view, download_image_view
from . import views

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("download-csv/", download_csv_view, name="download_csv"),
    path("download-image/<str:filename>/", download_image_view, name="download_image"),
    path('compare-prices/', views.compare_prices_view, name='compare_prices'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
]
