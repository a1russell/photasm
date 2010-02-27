import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from PIL import Image
import pyexiv2

from photasm.photos.models import Album, Photo, PhotoTag


class AddPhotoTest(TestCase):
    file_format = 'JPEG'
    file_suffix = '.jpg'
    is_jpeg = True

    def setUp(self):
        self.user = User.objects.create_user('adam', 'adam@example.com',
                                             'adampassword')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='adam', password='adampassword')
        self.album = Album.objects.create(owner=self.user, name='Test')

        image_fd, self.image_path = tempfile.mkstemp(suffix=self.file_suffix)
        os.close(image_fd)
        Image.new('RGB', (640, 480)).save(self.image_path, self.file_format)

        metadata = pyexiv2.Image(self.image_path)
        metadata.readMetadata()
        metadata['Exif.Image.ImageDescription'] = 'test image'
        metadata['Exif.Image.Artist'] = 'Adam'
        metadata.writeMetadata()

    def tearDown(self):
        os.remove(self.image_path)
        self.client.logout()
        User.objects.all().delete()
        Album.objects.all().delete()
        Photo.objects.all().delete()

    def test_form(self):
        photo_upload_url = reverse('photasm.photos.views.photo_upload')

        response = self.client.get(photo_upload_url)
        self.assertEqual(response.status_code, 200)

        image = open(self.image_path)
        response = self.client.post(photo_upload_url, {
            'album': self.album.id, 'image': image})
        image.close()
        photos = Photo.objects.order_by('-id')
        self.assertTrue(len(photos))
        photo = photos[0]
        self.assertRedirects(response, photo.get_absolute_url())
        # Photo has already been synced
        self.assertFalse(photo.sync_metadata_from_file())
        self.assertEqual(photo.description, 'test image')
        self.assertEqual(photo.is_jpeg, self.is_jpeg)
        self.assertEqual(photo.owner, self.user)
        self.assertEqual(Image.open(photo.thumbnail.path).format,
                         self.file_format)

        response = self.client.post(photo_upload_url, {})
        # Get page back with error message
        self.assertEqual(response.status_code, 200)

    def test_admin_form(self):
        photo_upload_url = '/admin/photos/photo/add/'

        image = open(self.image_path)
        response = self.client.post(photo_upload_url, {
            'owner': self.user.id,
            'album': self.album.id,
            'image': image,
            'description': 'image for testing',
            'metadata_sync_enabled': True,
        })
        image.close()
        photos = Photo.objects.order_by('-id')
        self.assertTrue(len(photos))
        photo = photos[0]
        self.assertEqual(response.status_code, 302)

        self.assertFalse(photo.sync_metadata_from_file())
        self.assertEqual(photo.description, 'image for testing')
        self.assertEqual(photo.artist, 'Adam')
        self.assertEqual(photo.is_jpeg, self.is_jpeg)
        self.assertEqual(photo.owner, self.user)
        self.assertEqual(Image.open(photo.thumbnail.path).format,
                         self.file_format)
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'image for testing')
        self.assertEqual(metadata['Exif.Image.Artist'],
                         'Adam')


class AddTIFFTest(AddPhotoTest):
    file_format = 'TIFF'
    file_suffix = '.tif'
    is_jpeg = False


class EditPhotoTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('adam', 'adam@example.com',
                                             'adampassword')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='adam', password='adampassword')
        self.album = Album.objects.create(owner=self.user, name='Test')
        self.keyword = PhotoTag.objects.create(name='test')

        image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        Image.new('RGB', (640, 480)).save(image_path, 'JPEG')

        self.photo = Photo()
        self.photo.owner = self.user
        self.photo.album = self.album
        image = open(image_path)
        self.photo.image = ImageFile(image)
        self.photo.is_jpeg = True
        self.photo.save()
        os.remove(image_path)

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Album.objects.all().delete()
        PhotoTag.objects.all().delete()
        Photo.objects.all().delete()

    def test_form(self):
        photo_edit = 'photasm.photos.views.photo_edit'

        photo_edit_url = reverse(photo_edit, args=[0])
        response = self.client.get(photo_edit_url)
        self.assertEqual(response.status_code, 404)

        photo_edit_url = reverse(photo_edit, args=[self.photo.id])

        response = self.client.get(photo_edit_url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'album': self.album.id,
            'description': 'test image',
            'artist': 'Adam',
            'country': 'USA',
            'province_state': 'VA',
            'city': 'Blacksburg',
            'location': 'Drillfield',
            'time_created': '2007-09-28 03:00:00',
            'keywords': self.keyword.id,
        }
        response = self.client.post(photo_edit_url, post_data)
        self.photo = Photo.objects.get(id=self.photo.id)
        self.assertRedirects(response, self.photo.get_absolute_url())
        self.assertFalse(self.photo.sync_metadata_to_file())
        self.assertEqual(self.photo.description, 'test image')

        response = self.client.post(photo_edit_url, {})
        self.assertEqual(response.status_code, 200)

    def test_admin_form(self):
        photo_edit_url = '/admin/photos/photo/%d/' % self.photo.id

        post_data = {
            'owner': self.user.id,
            'album': self.album.id,
            'description': 'test image',
            'artist': 'Adam',
            'country': 'USA',
            'province_state': 'VA',
            'city': 'Blacksburg',
            'location': 'Drillfield',
            'time_created': '2007-09-28 03:00:00',
            'keywords': self.keyword.id,
            'metadata_sync_enabled': True,
            '_save': 'Save',
        }
        response = self.client.post(photo_edit_url, post_data)
        self.photo = Photo.objects.get(id=self.photo.id)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.photo.sync_metadata_to_file())
        self.assertEqual(self.photo.description, 'test image')


class PhotoDetailTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('adam', 'adam@example.com',
                                        'adampassword')
        self.client.login(username='adam', password='adampassword')
        album = Album.objects.create(owner=user, name='Test')
        # TODO: Remove this line.
        keyword = PhotoTag.objects.create(name='test')

        image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        Image.new('RGB', (640, 480)).save(image_path, 'JPEG')

        self.photo = Photo()
        self.photo.owner = user
        self.photo.album = album
        image = open(image_path)
        self.photo.image = ImageFile(image)
        self.photo.is_jpeg = True
        self.photo.description = 'test image'
        self.photo.artist = 'Adam'
        self.photo.country = 'USA'
        self.photo.province_state = 'VA'
        self.photo.city = 'Blacksburg'
        self.photo.location = 'Drillfield'
        self.photo.time_created = datetime.datetime(2007, 9, 28, 3, 0)
        self.photo.save()
        os.remove(image_path)
        self.photo.set_keywords(['test', 'photo'])
        self.photo.save()

    def tearDown(self):
        self.client.logout()
        User.objects.all().delete()
        Album.objects.all().delete()
        PhotoTag.objects.all().delete()
        Photo.objects.all().delete()

    def test_view(self):
        photo_detail = 'photasm.photos.views.photo_detail'

        photo_detail_url = reverse(photo_detail, args=[self.photo.id])
        response = self.client.get(photo_detail_url)
        self.assertEqual(response.status_code, 200)
