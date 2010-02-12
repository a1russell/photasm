import os
import tempfile

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from PIL import Image

from photasm.photos.models import Album


class AddPhotoTest(TestCase):
    def setUp(self):
        User.objects.all().delete()
        Album.objects.all().delete()

        self.user = User.objects.create_user('adam', 'adam@example.com',
                                             'adampassword')
        self.client.login(username='adam', password='adampassword')
        self.album = Album.objects.create(owner=self.user, name='Test')

        image_fd, self.image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        Image.new('RGB', (640, 480)).save(self.image_path, 'JPEG')

    def tearDown(self):
        os.remove(self.image_path)
        self.client.logout()

    def test_forms(self):
        photo_upload_url = reverse('photasm.photos.views.photo_upload')

        response = self.client.get(photo_upload_url)
        self.assertEqual(response.status_code, 200)

        image = open(self.image_path)
        response = self.client.post(photo_upload_url,
                                    {'album': self.album.id, 'image': image })
        image.close()
        # Redirect on form sucess
        self.assertEqual(response.status_code, 302)

        response = self.client.post(photo_upload_url, {})
        # Get page back with error message
        self.assertEqual(response.status_code, 200)

