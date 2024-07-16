from django.urls import path
from .views import (test_endpoint,
                    upload_image,
                    download_image,
                    analyze_image,
                    get_analysis_result)

urlpatterns = [
    path('ping/', test_endpoint, name='test_endpoint'),
    path('images/upload/', upload_image, name='upload_image'),
    path('images/<str:filename>/', download_image, name='download_image'),
    path('analysis/', analyze_image, name='analyze_image'),
    path('analysis/', get_analysis_result, name='get_analysis_result'),
]
