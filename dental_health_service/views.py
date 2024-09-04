# -*- coding: utf-8 -*-

# Standard libraries section
import re
from datetime import datetime, timedelta, timezone

# Django section
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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


@csrf_exempt
@api_view(['POST'])
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
                TextMessage(text='請輸入日期\n(格式：2024/07/01 或 2024.08.02)')
            ]
        else:

            if match_text := re.search(r'\d{4}[-/.]\d{2}[-/.]\d{2}', user_message):
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
        # TODO: if receiving multiple requests within a second, service might be failed!!
        folder_name = gmt_plus8_time.strftime('%Y-%m-%d_%H-%M-%S')
        save_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / folder_name
        save_path.mkdir(parents=True, exist_ok=True)

        # save image
        image_path = save_path / 'original_image.png'
        default_storage.save(str(image_path), ContentFile(image_content))

        try:
            # Invoke analysis API for image processing
            result_comment = DentalPlaqueAnalysis.analyze_dental_plaque(save_path)
        except Exception as e:
            logger.error(f"Error during dental plaque analysis: {e}")
            result_comment = None

        if result_comment:
            domain_name = 'https://dental-service.jieniguicare.org'
            api_route = '/api/analysis/'
            teeth_range_path = domain_name + api_route + f'teeth_range/{folder_name}/'
            teeth_range_detect_path = domain_name + api_route + f'teeth_range_detect/{folder_name}/'

            # Integrate all the messages
            messages = [
                TextMessage(text=f'日期：{folder_name}'),
                ImageMessage(
                    original_content_url=teeth_range_path,
                    preview_image_url=teeth_range_path),
                ImageMessage(
                    original_content_url=teeth_range_detect_path,
                    preview_image_url=teeth_range_detect_path),
                TextMessage(text=result_comment)
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
@timelog
def test_endpoint(request):
    """For checking API endpoint is working."""
    logger.info('[GET]Response message: Hi there, API is working~')
    return Response({"message": "Hi there, API is working~"})


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
@timelog
def analyze_image(request):

    # return Response({"message": "Test view accessed"}, status=status.HTTP_200_OK)

    if 'image' not in request.FILES:
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']

    # Get the current UTC time and convert to GMT+8 time zone
    gmt_plus8_time = datetime.now(timezone.utc) + timedelta(hours=8)
    # TODO: if receiving multiple requests within a second, service might be failed!!
    folder_name = gmt_plus8_time.strftime('%Y-%m-%d_%H-%M-%S')
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
@timelog
def get_analysis_result(request, image_name, timestamp):
    valid_image_types = ['teeth_range', 'teeth_range_detect']
    if image_name not in valid_image_types:
        raise Http404

    image_path = settings.MEDIA_ROOT / 'dental_plaque_analysis' / timestamp / f'{image_name}.png'
    if not image_path.exists():
        raise Http404

    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')

