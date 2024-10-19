from django.urls import path
from .views import (test_endpoint,
                    test_jwt_permission,
                    upload_image,
                    download_image,
                    analyze_image,
                    get_analysis_result,
                    callback,
                    list_teeth_cleaning_records,
                    edit_single_cleaning_records,
                    list_teeth_cleaning_records_for_student,
                    list_teeth_cleaning_records_by_date)

urlpatterns = [
    path('ping/', test_endpoint, name='test_endpoint'),
    path('test_jwt/', test_jwt_permission, name='test_jwt_permission'),
    path('images/upload/', upload_image, name='upload_image'),
    path('images/<str:filename>/', download_image, name='download_image'),
    path('analysis/', analyze_image, name='analyze_image'),
    path('analysis/<str:image_name>/<str:timestamp>/', get_analysis_result, name='get_analysis_result'),
    path('linebot/callback/', callback, name='linebot_callback'),
    path('records/', list_teeth_cleaning_records, name='list_teeth_cleaning_records'),
    path('records/<int:pk>/', edit_single_cleaning_records, name='edit_single_cleaning_records'),
    path('records/students/<int:student_id>/', list_teeth_cleaning_records_for_student,
         name='list_teeth_cleaning_records_for_student'),
    path('records/date/<str:date>/', list_teeth_cleaning_records_by_date, name='list_teeth_cleaning_records_by_date'),
]
