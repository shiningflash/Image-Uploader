from __future__ import annotations

from django import forms


class ImageUploadForm(forms.Form):
    """
    Simple form for validating uploaded image.
    - Handles file validation (Pillow backend).
    """

    image = forms.ImageField()
