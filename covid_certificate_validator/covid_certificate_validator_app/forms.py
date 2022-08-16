from django import forms


class CertificateUploadForm(forms.Form):
    uploaded_file = forms.FileField()
