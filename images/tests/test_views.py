from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from images.models import ImageAsset

User = get_user_model()


class ImageUploadTests(TestCase):
    def setUp(self):
        # Create and login a test user
        self.user = User.objects.create_user(username="amir", password="amir123")
        self.client.login(username="amir", password="amir123")
        self.upload_url = reverse("image_upload")
        self.client_ip = "127.0.0.1"

    def _create_test_image(self, name="test.png"):
        """Generate a small 1x1 PNG image in memory."""
        file = BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(file, "PNG")
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type="image/png")

    def test_image_upload_success(self):
        """Uploading a valid image should create a record and redirect to detail page."""
        image = self._create_test_image()

        response = self.client.post(
            self.upload_url,
            {"image": image},
            REMOTE_ADDR=self.client_ip,
        )

        self.assertEqual(response.status_code, 302, response.content)
        self.assertEqual(ImageAsset.objects.count(), 1)

        image_obj = ImageAsset.objects.first()
        self.assertIn(str(image_obj.public_id), response.url)

    def test_upload_quota_per_ip(self):
        """Uploading more than 10 images in a day should block further uploads."""
        for i in range(10):
            image = self._create_test_image(name=f"test_{i}.png")
            self.client.post(
                self.upload_url,
                {"image": image},
                REMOTE_ADDR=self.client_ip,
            )

        # 11th upload should fail (quota exceeded)
        image = self._create_test_image(name="exceed.png")
        response = self.client.post(
            self.upload_url,
            {"image": image},
            REMOTE_ADDR=self.client_ip,
        )

        self.assertEqual(response.status_code, 429)
        self.assertIn(b"Daily quota reached", response.content)

    def test_only_uploader_can_delete(self):
        """Only the logged-in user who uploaded the image can delete it."""
        # Upload an image
        image = self._create_test_image()
        self.client.post(
            self.upload_url,
            {"image": image},
            REMOTE_ADDR=self.client_ip,
        )
        image_obj = ImageAsset.objects.first()
        delete_url = reverse("image_delete", args=[image_obj.public_id])

        # Delete as uploader
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ImageAsset.objects.count(), 0)

        # Re-upload as original user
        image = self._create_test_image(name="second.png")
        self.client.post(
            self.upload_url,
            {"image": image},
            REMOTE_ADDR=self.client_ip,
        )
        image_obj = ImageAsset.objects.first()

        # Logout original user
        self.client.logout()

        # Create a new user and login
        other_user = User.objects.create_user(username="other", password="other123")
        self.client.login(username="other", password="other123")

        # Try deleting as a different user — should fail
        delete_url = reverse("image_delete", args=[image_obj.public_id])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ImageAsset.objects.count(), 1)
