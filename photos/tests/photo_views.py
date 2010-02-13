import os
import tempfile

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from PIL import Image
import pyexiv2

from photasm.photos.models import Album, Photo


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

        metadata = pyexiv2.Image(self.image_path)
        metadata.readMetadata()
        metadata['Exif.Image.ImageDescription'] = 'test image'
        metadata.writeMetadata()

    def tearDown(self):
        os.remove(self.image_path)
        self.client.logout()

    def test_form(self):
        photo_upload_url = reverse('photasm.photos.views.photo_upload')

        response = self.client.get(photo_upload_url)
        self.assertEqual(response.status_code, 200)

        image = open(self.image_path)
        response = self.client.post(photo_upload_url,
                                    {'album': self.album.id, 'image': image })
        image.close()
        photos = Photo.objects.order_by('-id')
        self.assertTrue(len(photos))
        photo = photos[0]
        self.assertRedirects(response, photo.get_absolute_url())
        # Photo has already been synced
        self.assertFalse(photo.sync_metadata_from_file())
        self.assertEqual(photo.description, 'test image')
        self.assertTrue(photo.is_jpeg)
        self.assertEqual(photo.owner, self.user)
        self.assertEqual(Image.open(photo.thumbnail.path).format, 'JPEG')

        # TODO: Repeat the above test for an image that is not a JPEG.

        response = self.client.post(photo_upload_url, {})
        # Get page back with error message
        self.assertEqual(response.status_code, 200)

