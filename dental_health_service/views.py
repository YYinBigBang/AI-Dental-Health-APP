
from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .utils import logger, timelog

logger.info("========= Starting the API service =========")


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
    save_path = Path(settings.MEDIA_ROOT) / 'dental_plaque_analysis' / folder_name
    save_path.mkdir(parents=True, exist_ok=True)

    # save image
    image_path = save_path / 'original_image.png'
    default_storage.save(str(image_path), ContentFile(image.read()))

    results = {"percentage": '50'}  # TODO: invoking analyzed API for image processing

    return Response({
        'data': results,
        'message': f'整口牙齒的牙菌斑占百分比: {results["percentage"]}%'
    }, status=status.HTTP_201_CREATED)
