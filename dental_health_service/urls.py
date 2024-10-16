from django.urls import path
from .views import (test_endpoint,
                    test_jwt_permission,
                    upload_image,
                    download_image,
                    analyze_image,
                    get_analysis_result,
                    callback,
                    teeth_cleaning_record_list,
                    teeth_cleaning_record_detail)

urlpatterns = [
    path('ping/', test_endpoint, name='test_endpoint'),
    path('test_jwt/', test_jwt_permission, name='test_jwt_permission'),
    path('images/upload/', upload_image, name='upload_image'),
    path('images/<str:filename>/', download_image, name='download_image'),
    path('analysis/', analyze_image, name='analyze_image'),
    path('analysis/<str:image_name>/<str:timestamp>/', get_analysis_result, name='get_analysis_result'),
    path('linebot/callback/', callback, name='linebot_callback'),
    path('teeth-cleaning-records/', teeth_cleaning_record_list, name='teeth_cleaning_record_list'),
    path('teeth-cleaning-records/<int:pk>/', teeth_cleaning_record_detail, name='teeth_cleaning_record_detail'),
]
