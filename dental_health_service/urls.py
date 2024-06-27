from django.urls import path
from . import views

urlpatterns = [
    path('images/upload/', views.upload_image, name='upload_image'),
    path('images/<str:filename>/', views.get_image, name='get_image'),
]
