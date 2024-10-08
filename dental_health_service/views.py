# -*- coding: utf-8 -*-

# Standard libraries section
import re
import uuid
from functools import wraps
from datetime import datetime, timedelta, timezone

# Django section
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from .models import TeethCleaningRecord
from user_management.models import StudentProfile, User

# Rest Framework section
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

# LineBot section
from linebot.v3 import WebhookHandler, WebhookParser
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
from .django_utils import logger, timelog
from .ai_integrations.plaque_detection import DentalPlaqueAnalysis

logger.info("========= Starting the API service =========")
line_bot_config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
line_bot_handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


class UnauthorizedAccessException(Exception):
    """Exception raised when an unauthorized user attempts to access a protected resource."""
    pass


@csrf_exempt
@api_view(['POST'])
def callback(request):
    """The endpoint for receiving LINE messages."""
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')

    try:
        line_bot_handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning('Invalid signature. Please check your channel access token/channel secret.')
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_200_OK)


def user_authentication(func):
    """A decorator to validate the user before handling the request."""
    @wraps(func)
    def wrapper(event, *args, **kwargs):
        user_id = event.source.user_id
        try:
            user = User.objects.get(line_id=user_id)
            return func(event, *args, **kwargs)
        except User.DoesNotExist:
            logger.info('LINE user not found in the database!')
            with ApiClient(line_bot_config) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text='您的LINE帳號尚未註冊於系統！'),
                            TextMessage(text='請先向管理者註冊後再使用此功能，謝謝！')
                        ]
                    )
                )
            return None
        except Exception as e:
            logger.error(f'Error occurred during user validation: {e}')
            return None
    return wrapper


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
                TextMessage(text='請輸入日期\n(格式：2024-07-07_20-13-14_91adff)')
            ]
        else:
            regex = r'\d{4}[-./]\d{2}[-./]\d{2}[-._/]\d{2}[-./]\d{2}[-./]\d{2}[_]\w{6}'
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
        # Retrieve the user from the event
        line_user_id = event.source.user_id
        image_content = line_bot_blob_api.get_message_content(message_id=event.message.id)

        # Show loading animation
        try:
            loading_request = ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=25)
            line_bot_api.show_loading_animation(loading_request)
        except Exception as e:
            logger.warning('LinBot loading animation failure!')

        for _ in range(1):
            # Get the current UTC time and convert to GMT+8 time zone
            gmt_plus8_time = datetime.now(timezone.utc) + timedelta(hours=8)
            # Get first 6 characters of the UUID
            unique_id = str(uuid.uuid4())[:6]
            # add uuid to the folder name to avoid duplication
            folder_name = gmt_plus8_time.strftime('%Y-%m-%d_%H-%M-%S') + '_' + unique_id
            save_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / folder_name
            save_path.mkdir(parents=True, exist_ok=True)
            image_path = save_path / 'original_image.png'
            # save image
            default_storage.save(str(image_path), ContentFile(image_content))

            try:
                # Invoke analysis API for image processing
                result_comment = DentalPlaqueAnalysis.analyze_dental_plaque(save_path)
                if not result_comment:
                    raise Exception('API returned empty result')
            except Exception as e:
                result_comment = '圖片分析失敗！'
                logger.error(f"Error during dental plaque analysis: {e}")
                messages = [TextMessage(text=result_comment)]
                break

            # Prepare the image path for sending to client
            domain_name = 'https://dental-service.jieniguicare.org'
            api_route = '/api/analysis/'
            teeth_range_path = domain_name + api_route + f'teeth_range/{folder_name}/'
            teeth_range_detect_path = domain_name + api_route + f'teeth_range_detect/{folder_name}/'

            # Integrate all the messages for sending to client
            messages = [
                TextMessage(text=f'時間：{folder_name}'),
                ImageMessage(
                    original_content_url=teeth_range_path,
                    preview_image_url=teeth_range_path),
                ImageMessage(
                    original_content_url=teeth_range_detect_path,
                    preview_image_url=teeth_range_detect_path),
                TextMessage(text=result_comment)
            ]

        # Create the TeethCleaningRecord
        user = User.objects.get(line_id=line_user_id)
        student = StudentProfile.objects.get(user=user)
        teeth_cleaning_record = TeethCleaningRecord(
            student=student,
            date_time=gmt_plus8_time,
            images_path=folder_name,
            dental_plaque_count=result_comment
        )
        # Save the record to the database
        teeth_cleaning_record.save()

        # Send all the messages to client
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
    return Response({"message": "Hi there, API is working~"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@timelog
def test_jwt_permission(request):
    """A test endpoint to check if the JWT permission is working."""
    logger.info('[GET]Response message: Greetings, you have permission to access this endpoint')
    return Response({"message": "Greetings, you have permission to access this endpoint"})


@api_view(['POST'])
@timelog
def upload_image(request):

    if 'image' not in request.FILES:
        logger.warning('[POST]Response error: No image provided')
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']

    image_path = settings.MEDIA_ROOT / 'teeth' / image.name
    default_storage.save(str(image_path), ContentFile(image.read()))

    return Response({"message": "Image uploaded successfully"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
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
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

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
        result = DentalPlaqueAnalysis.analyze_dental_plaque(save_path)
    except Exception as e:
        logger.error(f"Error during dental plaque analysis: {e}")
        return Response({
            "error": "An error occurred during analysis"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    teeth_range_path = f'teeth_range/{folder_name}/'
    teeth_range_detect_path = f'teeth_range_detect/{folder_name}/'

    return Response({
        'message': result,
        'data': {
            'teethRangePath': teeth_range_path,
            'teethRangeDetectPath': teeth_range_detect_path
        }
    }, status=status.HTTP_201_CREATED)


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

