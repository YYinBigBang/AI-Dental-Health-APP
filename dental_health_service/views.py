# -*- coding: utf-8 -*-

# Standard libraries section
import re
import uuid
from datetime import datetime, timedelta, timezone

# Django section
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from .models import TeethCleaningRecord
from .serializers import TeethCleaningRecordSerializer
from user_management.models import StudentProfile

# Rest Framework section
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

# LineBot section
from linebot.v3 import WebhookHandler
from linebot.v3.messaging.api.messaging_api_blob import MessagingApiBlob
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ShowLoadingAnimationRequest,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage
)

# Custom section
from AI_Dental_Health_APP.django_utils import logger, timelog, standard_response
from .ai_integrations.plaque_detection import DentalPlaqueAnalysis

logger.info("========= Starting the API service =========")
line_bot_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
line_bot_handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def callback(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')

    try:
        line_bot_handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning('Invalid signature. Please check your channel access token/channel secret.')
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_200_OK)


@line_bot_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(line_bot_config) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_message = event.message.text

        # Show loading animation
        try:
            loading_request = ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=10)
            line_bot_api.show_loading_animation(loading_request)
        except Exception as e:
            logger.warning('LinBot loading animation failure!')

        if '潔牙偵測' in user_message:
            messages = [
                TextMessage(text='請上傳圖片')
            ]
        elif '查詢結果' in user_message:
            messages = [
                TextMessage(text='請輸入日期\n(格式：2024-10-21_07-01-59_4fb29d)')
            ]
        else:
            regex = r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[a-f0-9]{6}'
            if match_text := re.search(regex, user_message):
                timestamp = match_text.group()
                image_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / timestamp

                # Check if the analysis record exists
                if image_path.exists():
                    domain_name = 'https://dental-service.jieniguicare.org'
                    api_route = '/api/analysis/'
                    teeth_range_path = domain_name + api_route + f'teeth_range/{timestamp}/'
                    teeth_range_detect_path = domain_name + api_route + f'teeth_range_detect/{timestamp}/'
                    messages = [
                        ImageMessage(
                            original_content_url=teeth_range_path,
                            preview_image_url=teeth_range_path),
                        ImageMessage(
                            original_content_url=teeth_range_detect_path,
                            preview_image_url=teeth_range_detect_path)
                    ]
                else:
                    messages = [
                        TextMessage(text='沒有此筆資料！')
                    ]
            # Wrong date format
            else:
                messages = [
                    TextMessage(text='查詢日期格式錯誤')
                ]

        # Reply message to user
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages)
        )


@line_bot_handler.add(MessageEvent, message=ImageMessageContent)
def handle_content_message(event):
    with ApiClient(line_bot_config) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)
        image_content = line_bot_blob_api.get_message_content(message_id=event.message.id)

        # Show loading animation
        try:
            loading_request = ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=25)
            line_bot_api.show_loading_animation(loading_request)
        except Exception as e:
            logger.warning('LinBot loading animation failure!')

        # Get the current UTC time and convert to GMT+8 time zone
        gmt_plus8_time = datetime.now(timezone.utc) + timedelta(hours=8)
        # Get first 6 characters of the UUID
        unique_id = str(uuid.uuid4())[:6]
        # add uuid to the folder name to avoid duplication
        folder_name = gmt_plus8_time.strftime('%Y-%m-%d_%H-%M-%S') + '_' + unique_id
        save_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / folder_name
        save_path.mkdir(parents=True, exist_ok=True)

        # save image
        image_path = save_path / 'original_image.png'
        default_storage.save(str(image_path), ContentFile(image_content))

        try:
            # Invoke analysis API for image processing
            result_dict = DentalPlaqueAnalysis.analyze_dental_plaque(save_path)
        except Exception as e:
            logger.error(f"Error during dental plaque analysis: {e}")

        if result_dict.get('returncode', 1) == 0:
            domain_name = 'https://dental-service.jieniguicare.org'
            api_route = '/api/analysis/'
            teeth_range_path = domain_name + api_route + f'teeth_range/{folder_name}/'
            teeth_range_detect_path = domain_name + api_route + f'teeth_range_detect/{folder_name}/'

            # Integrate all the messages
            messages = [
                TextMessage(text=f'時間：{folder_name}'),
                ImageMessage(
                    original_content_url=teeth_range_path,
                    preview_image_url=teeth_range_path),
                ImageMessage(
                    original_content_url=teeth_range_detect_path,
                    preview_image_url=teeth_range_detect_path),
                TextMessage(text=result_dict.get('message', ''))
            ]
        else:
            messages = [TextMessage(text='圖片分析失敗！')]

        # Send all messages to client
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages)
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@timelog
def test_endpoint(request):
    """A test endpoint to check if the API is working."""
    logger.info('[GET]Response message: Hi there, API is working~')
    return standard_response(message="Hi there, API is working~")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@timelog
def test_jwt_permission(request):
    """A test endpoint to check if the JWT permission is working."""
    logger.info('[GET]Response message: Greetings, you have permission to access this endpoint')
    return standard_response(message="Greetings, you have permission to access this endpoint")


@api_view(['POST'])
@permission_classes([AllowAny])
@timelog
def upload_image(request):

    if 'image' not in request.FILES:
        logger.warning('[POST]Response error: No image provided')
        return standard_response(returncode=1, message="No image provided", status_code=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']

    image_path = settings.MEDIA_ROOT / 'teeth' / image.name
    default_storage.save(str(image_path), ContentFile(image.read()))

    return standard_response(message="Image uploaded successfully")


@api_view(['GET'])
@permission_classes([AllowAny])
@timelog
def download_image(request, filename):

    image_path = settings.MEDIA_ROOT / 'teeth' / filename
    if not image_path.exists():
        raise Http404

    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type="image/jpeg")


@api_view(['POST'])
@permission_classes([AllowAny])
@timelog
def analyze_image(request):
    """An endpoint to analyze the dental plaque in an image."""

    # return Response({"message": "Test view accessed"}, status=status.HTTP_200_OK)

    if 'image' not in request.FILES:
        return standard_response(returncode=1, message="No image provided", status_code=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']

    # Get the current UTC time and convert to GMT+8 time zone
    gmt_plus8_time = datetime.now(timezone.utc) + timedelta(hours=8)
    # Get first 6 characters of the UUID
    unique_id = str(uuid.uuid4())[:6]
    # add uuid to the folder name to avoid duplication
    folder_name = gmt_plus8_time.strftime('%Y-%m-%d_%H-%M-%S') + '_' + unique_id
    save_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / folder_name
    save_path.mkdir(parents=True, exist_ok=True)

    # save image
    image_path = save_path / 'original_image.png'
    default_storage.save(str(image_path), ContentFile(image.read()))

    try:
        # Invoking analyzed API for image processing
        result_dict = DentalPlaqueAnalysis.analyze_dental_plaque(save_path)
    except Exception as e:
        logger.error(f"Error during dental plaque analysis: {e}")
        return standard_response(
            returncode=1,
            message="An error occurred during analysis",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    teeth_range_path = f'teeth_range/{folder_name}/'
    teeth_range_detect_path = f'teeth_range_detect/{folder_name}/'

    return standard_response(
        message=result_dict.get('message', 'Dental plaque analysis completed'),
        data={
            'API status': result_dict.get('returncode', '-1'),
            'percentage_plaque_total': result_dict['data'].get('percentage_plaque_total', '-1'),
            'teethRangePath': teeth_range_path,
            'teethRangeDetectPath': teeth_range_detect_path
        },
        status_code=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
@timelog
def get_analysis_result(request, image_name, timestamp):
    """An endpoint to retrieve the analysis result images."""
    valid_image_types = ['teeth_range', 'teeth_range_detect']
    if image_name not in valid_image_types:
        raise Http404

    image_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / timestamp / f'{image_name}.png'
    if not image_path.exists():
        raise Http404

    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def get_authorized_student_ids(user):
    """Return the list of student IDs the user is authorized to access."""
    if hasattr(user, 'studentprofile'):
        return [user.studentprofile.id]
    elif hasattr(user, 'parent'):
        return user.parent.parentstudentrelationship_set.values_list('student_id', flat=True)
    elif hasattr(user, 'teacherprofile'):
        return StudentProfile.objects.filter(classroom__teachers=user.teacherprofile).values_list('id', flat=True)
    return []


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_teeth_cleaning_record(request):
    """Create a new teeth cleaning record."""
    serializer = TeethCleaningRecordSerializer(data=request.data)
    if serializer.is_valid():
        student = serializer.validated_data.get('student')
        user = request.user
        student_ids = get_authorized_student_ids(user)

        if student.id not in student_ids:
            return standard_response(
                returncode=1,
                message="此帳號無法新增潔牙紀錄",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer.save()
        return standard_response(
            message="潔牙紀錄創建成功",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return standard_response(
        returncode=1,
        message="無效資料格式",
        data=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teeth_cleaning_records(request):
    """A List all teeth cleaning records."""
    student_ids = get_authorized_student_ids(request.user)
    if not student_ids:
        return standard_response(
            returncode=1,
            message="此帳號無法查看潔牙紀錄",
            status_code=status.HTTP_403_FORBIDDEN
        )

    records = TeethCleaningRecord.objects.filter(student_id__in=student_ids)
    serializer = TeethCleaningRecordSerializer(records, many=True)
    return standard_response(
        message="Teeth cleaning records retrieved successfully",
        data=serializer.data
    )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def edit_single_cleaning_records(request, pk):
    """An endpoint to retrieve, update, or delete a teeth cleaning record."""
    try:
        record = TeethCleaningRecord.objects.get(pk=pk)
    except TeethCleaningRecord.DoesNotExist:
        return standard_response(
            returncode=1,
            message="找不到潔牙紀錄",
            status_code=status.HTTP_404_NOT_FOUND
        )

    user = request.user
    student_ids = get_authorized_student_ids(user)

    if record.student_id not in student_ids:
        return standard_response(
            returncode=1,
            message="無權限存取此紀錄",
            status_code=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        serializer = TeethCleaningRecordSerializer(record)
        return standard_response(
            message="Teeth cleaning record retrieved successfully",
            data=serializer.data
        )

    elif request.method == 'PUT':
        serializer = TeethCleaningRecordSerializer(record, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return standard_response(
                message="潔牙紀錄更新成功",
                data=serializer.data
            )
        return standard_response(
            returncode=1,
            message="無效資料格式",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        record.delete()
        return standard_response(
            message="此筆潔牙紀錄已刪除！！",
            status_code=status.HTTP_204_NO_CONTENT
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teeth_cleaning_records_for_student(request, student_id):
    """Retrieve all teeth cleaning records for a specific student."""
    user = request.user
    authorized_student_ids = get_authorized_student_ids(user)

    if student_id not in authorized_student_ids:
        return standard_response(
            returncode=1,
            message="此帳號無法查看指定學生的潔牙紀錄",
            status_code=403
        )

    try:
        records = TeethCleaningRecord.objects.filter(student_id=student_id)
        serializer = TeethCleaningRecordSerializer(records, many=True)
        return standard_response(
            message="Teeth cleaning records retrieved successfully",
            data=serializer.data
        )
    except TeethCleaningRecord.DoesNotExist:
        return standard_response(
            returncode=1,
            message="找不到潔牙紀錄",
            status_code=404
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teeth_cleaning_records_by_date(request, date):
    """Retrieve all teeth cleaning records for a specific date."""
    try:
        records = TeethCleaningRecord.objects.filter(date_time__date=date)
        serializer = TeethCleaningRecordSerializer(records, many=True)
        return standard_response(
            message="Teeth cleaning records for specified date retrieved successfully",
            data=serializer.data
        )
    except TeethCleaningRecord.DoesNotExist:
        return standard_response(
            returncode=1,
            message="找不到指定日期的潔牙紀錄",
            status_code=404
        )
