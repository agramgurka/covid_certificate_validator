import os
import logging
import sys
import time

from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .forms import CertificateUploadForm
from .services.certificate_validator import ValidationFormHandler


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.addHandler(handler)

START_TIME = 0


class CertificateUploadView(View):
    form_template = "validator_input_form.html"

    def get(self, request):
        form = CertificateUploadForm()
        context = {"form": form}
        return render(request, CertificateUploadView.form_template, context)

    def post(self, request):
        start_time = time.time()
        logger.debug("processing post request")
        form = CertificateUploadForm(request.POST, request.FILES)
        storage_location = os.path.join(settings.MEDIA_ROOT, "validation_temporary")
        fss = FileSystemStorage(location=storage_location)
        if form.is_valid():
            try:
                logger.debug(f"running certificate validation in {time.time() - start_time}")
                upload = request.FILES["uploaded_file"]
                validator = ValidationFormHandler(fss, upload)
                response = validator.get_response()
                context = {"response": response}
                logger.debug(f"validation is successfully completed in {time.time() - start_time}")
                return JsonResponse(response)
            except Exception as e:
                exception_json = {"VALIDATION ERROR: ": "LOOK TROUGH THE LOG"}
                logger.debug(f"validation is completed with error in {time.time() - start_time}")
                return JsonResponse(exception_json)
        else:
            context = {"form": form}
            logger.debug(f"validation is not possible due to form validity, finished in {time.time() - start_time}")
        return render(request, CertificateUploadView.form_template, context)

