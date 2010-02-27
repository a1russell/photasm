import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from PIL import Image

from photasm.photos.models import Album, Photo


LOGIN_URL = reverse('django.contrib.auth.views.login')


def get_login_url(original_url):
    """Gets the redirected login URL for the given original URL."""
    return "%s?next=%s" % (LOGIN_URL, original_url)


class PhotoUploadTest(TestCase):

    def runTest(self):
        photo_upload_url = reverse('photasm.photos.views.photo_upload')
        login_url = get_login_url(photo_upload_url)

        response = self.client.get(photo_upload_url)
        self.assertRedirects(response, login_url)


class PhotoTest(TestCase):

    def setUp(self):
        # Create an image.
        image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        Image.new('RGB', (1, 1)).save(image_path, 'JPEG')

        # Create a Photo object.
        user = User.objects.create(username="Adam")
        album = Album.objects.create(owner=user, name="Test")
        self.photo = Photo()
        self.photo.owner = user
        image = open(image_path)
        self.photo.image = ImageFile(image)
        self.photo.album = album
        self.photo.is_jpeg = True
        self.photo.save()
        image.close()
        os.remove(image_path)

    def tearDown(self):
        Photo.objects.all().delete()
        Album.objects.all().delete()
        User.objects.all().delete()

    def test_photo_edit(self):
        photo_edit = 'photasm.photos.views.photo_edit'
        photo_edit_url = reverse(photo_edit, args=[self.photo.id])
        login_url = get_login_url(photo_edit_url)

        response = self.client.get(photo_edit_url)
        self.assertRedirects(response, login_url)

    def test_home(self):
        home_url = reverse('photasm.photos.views.home')
        login_url = get_login_url(home_url)

        response = self.client.get(home_url)
        self.assertRedirects(response, login_url)
