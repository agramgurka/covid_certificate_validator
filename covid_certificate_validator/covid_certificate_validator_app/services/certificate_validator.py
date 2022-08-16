import os
import sys
import logging
import re
import time

import fitz
import cv2
import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.addHandler(handler)

START_TIME = 0

class FormatsConverter:
    """class implements formats conversions"""

    @staticmethod
    def get_png(file):
        """ return png file"""

        file = os.path.abspath(file)
        if file.endswith(".png"):
            file_png = file
        elif file.endswith(".pdf"):
            file_dir = os.path.dirname(file)
            file_name = os.path.basename(file).split(sep=".")[0]
            file_png = os.path.join(file_dir, file_name + '.png')
            logger.debug(f"start converting in {time.time() - START_TIME}")
            FormatsConverter.convert_pdf_to_png(file, file_png)
            logger.debug(f"finish converting in {time.time() - START_TIME}")
        else:
            logger.exception("incorrect file extension, not possible to convert to png")
            raise Exception
        return file_png

    @staticmethod
    def convert_pdf_to_png(pdf_path, png_path):
        """ convert pdf to png"""

        try:
            doc = fitz.Document(pdf_path)
            page = doc.load_page(0)
            picture = page.get_pixmap(dpi=300)
            picture.save(png_path)
        except Exception:
            logger.exception("it's not possible to convert file to png")
            raise


class QRCodeDecoder:
    """class implements qr-code decoder"""

    @staticmethod
    def decode(image):
        """ decode text from qrcode """

        qrcode = cv2.imread(image)
        if qrcode is None:
            try:
                image = FormatsConverter.get_png(image)
            except Exception:
                raise
            else:
                qrcode = cv2.imread(image)
                if qrcode is None:
                    raise Exception("image can't be read")
        detector = cv2.QRCodeDetector()
        decoded_text, vertices, _ = detector.detectAndDecode(qrcode)
        if vertices is None:
            logger.exception("qrcode wasn't detected")
            raise Exception
        logger.debug(f"decoded url: {decoded_text}")
        return decoded_text


class CertificateValidator:
    """ class represents a covid certificate validator """

    API_ADDRESS = "https://www.gosuslugi.ru/api/covid-cert-checker/v3/cert/status/"

    @staticmethod
    def validate(certificate_id):
        logger.debug(f"sending request to api in {time.time() - START_TIME}")
        request_url = CertificateValidator.API_ADDRESS + certificate_id
        response = requests.get(request_url)
        logger.debug(f"receiving response from the api in {time.time() - START_TIME}")
        return response.json()


class ValidationFormHandler:
    """class handles validation form"""

    def __init__(self, fss, upload):
        global START_TIME
        START_TIME = time.time()
        self.fss = fss
        file = fss.save(upload.name, upload)
        self.file = fss.path(file)
        logger.debug(f"finish file storage initialization in {time.time() - START_TIME}")

    def get_response(self):
        logger.debug(f"start decoding in {time.time() - START_TIME}")
        decoded_url = QRCodeDecoder.decode(self.file)
        logger.debug(f"finish decoding in {time.time() - START_TIME}")
        search_pattern = re.compile("(?<=status/)(\w|-)+(?=\?lang)")
        certificate_id_match = search_pattern.search(decoded_url)
        if certificate_id_match:
            certificate_id = certificate_id_match.group()
            response = CertificateValidator.validate(certificate_id)
            logger.debug(f"start deleting in {time.time() - START_TIME}")
            self.delete_temporary_files()
            logger.debug(f"finish deleting files in {time.time() - START_TIME}")
            return response
        else:
            logger.exception("no match for certificate id pattern was found")
            self.delete_temporary_files()
            raise Exception

    def delete_temporary_files(self):
        for file in self.fss.listdir(self.fss.location)[1]:
            self.fss.delete(file)

