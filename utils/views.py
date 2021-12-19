import os
from pathlib import Path
from django.conf import settings
from account.serializers import ImageUploadForm, FileUploadForm
from utils.shortcuts import rand_str
from utils.api import CSRFExemptAPIView
import logging

logger = logging.getLogger(__name__)


class SimditorImageUploadAPIView(CSRFExemptAPIView):
    request_parsers = ()

    def post(self, request):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data["image"]
        else:
            return self.response({
                "success": False,
                "msg": "Upload failed",
                "file_path": ""})

        suffix = os.path.splitext(img.name)[-1].lower()
        if suffix not in [".gif", ".jpg", ".jpeg", ".bmp", ".png"]:
            return self.response({
                "success": False,
                "msg": "Unsupported file format",
                "file_path": ""})
        img_dir = rand_str(10)
        Path(os.path.join(settings.UPLOAD_DIR, img_dir)).mkdir(parents=True, exist_ok=True)
        try:
            with open(os.path.join(settings.UPLOAD_DIR, img_dir, img.name), "wb") as imgFile:
                for chunk in img:
                    imgFile.write(chunk)
        except IOError as e:
            logger.error(e)
            return self.response({
                "success": False,
                "msg": "Upload Error",
                "file_path": ""})
        return self.response({
            "success": True,
            "msg": "Success",
            "file_path": f"{settings.UPLOAD_PREFIX}/{img_dir}/{img.name}"})


class SimditorFileUploadAPIView(CSRFExemptAPIView):
    request_parsers = ()

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
        else:
            return self.response({
                "success": False,
                "msg": "Upload failed"
            })

        suffix = os.path.splitext(file.name)[-1].lower()
        file_dir = rand_str(10)
        Path(os.path.join(settings.UPLOAD_DIR, file_dir)).mkdir(parents=True, exist_ok=True)
        try:
            with open(os.path.join(settings.UPLOAD_DIR, file_dir, file.name), "wb") as f:
                for chunk in file:
                    f.write(chunk)
        except IOError as e:
            logger.error(e)
            return self.response({
                "success": False,
                "msg": "Upload Error"})
        return self.response({
            "success": True,
            "msg": "Success",
            "file_path": f"{settings.UPLOAD_PREFIX}/{file_dir}/{file.name}",
            "file_name": file.name})
