import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from PIL import Image

from photasm.photos.models import Album, Photo


class ViewTest(TestCase):

    def setUp(self):
        # Create an image.
        image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        Image.new('RGB', (1, 1)).save(image_path, 'JPEG')

        # Create a Photo object.
        user = User.objects.create_user('adam', 'adam@example.com',
                                        'adampassword')
        album = Album.objects.create(owner=user, name="Test")
        photo = Photo()
        photo.owner = user
        image = open(image_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = True
        photo.save()
        image.close()
        os.remove(image_path)

        self.client.login(username='adam', password='adampassword')

    def tearDown(self):
        self.client.logout()
        Photo.objects.all().delete()
        Album.objects.all().delete()
        User.objects.all().delete()

    def test_home(self):
        home_url = reverse('photasm.photos.views.home')

        response = self.client.get(home_url)
        self.assertEqual(response.status_code, 200)
