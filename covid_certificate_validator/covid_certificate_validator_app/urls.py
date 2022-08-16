from django.urls import path
from covid_certificate_validator_app.views import CertificateUploadView

urlpatterns = [
    path('', CertificateUploadView.as_view(), name="Certificate uploaded form")
]
