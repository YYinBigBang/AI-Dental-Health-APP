from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import HttpResponse, Http404
from pathlib import Path

@api_view(['POST'])
def upload_image(request):
    if 'image' not in request.FILES:
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']
    image_path = settings.MEDIA_ROOT / 'teeth' / image.name

    with open(image_path, 'wb+') as f:
        for chunk in image.chunks():
            f.write(chunk)

    return Response({"message": "Image uploaded successfully"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_image(request, filename):
    image_path = settings.MEDIA_ROOT / 'teeth' / filename
    if not image_path.exists():
        raise Http404

    with open(image_path, 'rb') as f:
        return HttpResponse(f.read(), content_type="image/jpeg")