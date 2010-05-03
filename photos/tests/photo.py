import datetime
import os
import tempfile

from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.test import TestCase
from PIL import Image
import pyexiv2

from photasm.photos.models import Album, Photo, PhotoTag


class KeywordsTest(TestCase):

    def setUp(self):
        # Create an image.
        file_descriptor, self.file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(self.file_path, 'JPEG')

    def tearDown(self):
        os.remove(self.file_path)
        User.objects.all().delete()
        Album.objects.all().delete()
        PhotoTag.objects.all().delete()
        Photo.objects.all().delete()

    def test_get(self):
        # Create a Photo object.
        photo = Photo()
        owner = User.objects.create(username='Adam')
        album = Album.objects.create(name='test', owner=owner)
        test_kw = PhotoTag.objects.create(name="test")
        photo_kw = PhotoTag.objects.create(name="photo")
        photo.owner = owner
        photo.album = album
        image = open(self.file_path)
        photo.image = ImageFile(image)
        photo.save()
        image.close()

        # Photo has empty list of keywords.
        self.assertEqual(photo.keyword_list, [])

        # Add some keywords.
        photo.keywords.add(test_kw)
        photo.keywords.add(photo_kw)
        photo.save()
        self.assertEqual(photo.keyword_list, [u'test', u'photo'])

    def test_set(self):
        # Create a Photo object.
        test_kw = PhotoTag.objects.create(name="test")
        photo = Photo()
        owner = User.objects.create(username='Adam')
        album = Album.objects.create(name='test', owner=owner)
        photo.owner = owner
        photo.album = album
        image = open(self.file_path)
        photo.image = ImageFile(image)
        photo.save()
        image.close()
        self.assertEqual(test_kw.photo_set.count(), 0)
        # Reminder: Database is assumed to be empty at the start of this test.
        self.assertEqual(PhotoTag.objects.count(), 1)

        # Set the photo's keywords.
        photo.keyword_list = ['Test', 'photo']
        photo.save()
        self.assertEqual(photo.keyword_list, [u'test', u'photo'])
        self.assertEqual(test_kw.photo_set.count(), 1)
        self.assertEqual(PhotoTag.objects.count(), 2)

        # Set the photo's keywords to something completely different.
        photo.keyword_list = ['foo', 'bar']
        photo.save()
        self.assertEqual(photo.keyword_list, [u'foo', u'bar'])
        self.assertEqual(test_kw.photo_set.count(), 0)
        self.assertEqual(PhotoTag.objects.count(), 4)

        # Set the photo's keywords to an empty list.
        photo.keyword_list = []
        photo.save()
        self.assertEqual(photo.keyword_list, [])


class CreateThumbnailTest(TestCase):

    def runTest(self):
        # Create a JPEG with an embedded thumbnail.
        image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
        os.close(image_fd)
        thumb_fd, thumb_path = tempfile.mkstemp(suffix='.jpg')
        os.close(thumb_fd)
        image = Image.new('RGB', (640, 480))
        image.save(image_path, 'JPEG')
        thumb = image.copy()
        thumb.thumbnail((160, 120))
        thumb.save(thumb_path, 'JPEG')

        # Write the thumbnail to the image metadata.
        metadata = pyexiv2.Image(image_path)
        metadata.readMetadata()
        metadata.setThumbnailFromJpegFile(thumb_path)
        metadata.writeMetadata()
        os.remove(thumb_path)

        # Create Photo model object.
        user = User.objects.create(username="Adam")
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

        # Create and verify the thumbnail.
        photo.create_thumbnail()
        photo.save()
        thumb = Image.open(photo.thumbnail.path)
        self.assertEqual(thumb.size[0] * thumb.size[1], 19200)
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        embedded = metadata.getThumbnailData()[1]
        external = open(photo.thumbnail.path).read()
        self.assertEqual(embedded, external)

        # Test JPEG without thumbnail already embedded.
        image = Image.new('RGB', (640, 480))
        image.save(image_path, 'JPEG')
        photo = Photo()
        photo.owner = user
        image = open(image_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = True
        photo.save()
        image.close()
        os.remove(image_path)
        photo.create_thumbnail()
        photo.save()
        thumb = Image.open(photo.thumbnail.path)
        self.assertEqual(thumb.size[0] * thumb.size[1], 19200)
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        embedded = metadata.getThumbnailData()[1]
        external = open(photo.thumbnail.path).read()
        self.assertEqual(embedded, external)

        # Test BMP.
        image_fd, image_path = tempfile.mkstemp(suffix='.bmp')
        os.close(image_fd)
        image = Image.new('RGB', (640, 480))
        image.save(image_path, 'BMP')
        photo = Photo()
        photo.owner = user
        image = open(image_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = False
        photo.save()
        image.close()
        os.remove(image_path)
        photo.create_thumbnail()
        photo.save()
        thumb = Image.open(photo.thumbnail.path)
        self.assertEqual(thumb.size[0] * thumb.size[1], 19200)

        # Test small image.
        image = Image.new('RGB', (80, 60))
        image.save(image_path, 'JPEG')
        photo = Photo()
        photo.owner = user
        image = open(image_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = True
        photo.save()
        image.close()
        os.remove(image_path)
        self.assertEqual(photo.create_thumbnail(), None)
        photo.save()
        thumb = Image.open(photo.thumbnail.path)
        self.assertEqual(thumb.size, (80, 60))
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        embedded = metadata.getThumbnailData()[1]
        external = open(photo.thumbnail.path).read()
        self.assertEqual(embedded, external)

        User.objects.all().delete()
        Album.objects.all().delete()
        Photo.objects.all().delete()


class SyncMetadataToFileTest(TestCase):

    def runTest(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')

        # Create a Photo object.
        user = User.objects.create(username="Adam")
        album = Album.objects.create(owner=user, name="Test")
        photo = Photo()
        photo.owner = user
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.description = "Test file"
        photo.artist = "Adam"
        photo.country = "USA"
        photo.province_state = "Virginia"
        photo.city = "Blacksburg"
        photo.location = "Dreamland"
        photo.time_created = datetime.datetime(2007, 9, 28, 3, 0)
        photo.album = album
        photo.is_jpeg = True
        photo.save()
        image.close()
        os.remove(file_path)
        photo.keyword_list = ['test', 'photo']
        photo.save()

        # Synchronize.
        performed_sync = photo.sync_metadata_to_file()
        self.assertTrue(performed_sync)

        # Metadata should exist in the file itself.
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'], 'Test file')
        self.assertEqual(metadata['Exif.Image.Artist'], 'Adam')
        self.assertEqual(metadata['Iptc.Application2.CountryName'], 'USA')
        self.assertEqual(metadata['Iptc.Application2.ProvinceState'],
                         'Virginia')
        self.assertEqual(metadata['Iptc.Application2.City'], 'Blacksburg')
        self.assertEqual(metadata['Iptc.Application2.SubLocation'],
                         'Dreamland')
        self.assertEqual(str(metadata['Exif.Photo.DateTimeOriginal']),
                         '2007-09-28 03:00:00')
        self.assertEqual(metadata['Iptc.Application2.Keywords'],
                         ('test', 'photo'))
        self.assertEqual(metadata['Exif.Photo.PixelXDimension'], 1)
        self.assertEqual(metadata['Exif.Photo.PixelYDimension'], 1)

        # Attempt to synchronize again...
        self.assertFalse(photo.sync_metadata_to_file())
        # Nothing should have changed.
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'], 'Test file')
        self.assertEqual(metadata['Exif.Image.Artist'], 'Adam')
        self.assertEqual(metadata['Iptc.Application2.CountryName'], 'USA')
        self.assertEqual(metadata['Iptc.Application2.ProvinceState'],
                         'Virginia')
        self.assertEqual(metadata['Iptc.Application2.City'], 'Blacksburg')
        self.assertEqual(metadata['Iptc.Application2.SubLocation'],
                         'Dreamland')
        self.assertEqual(str(metadata['Exif.Photo.DateTimeOriginal']),
                         '2007-09-28 03:00:00')
        self.assertEqual(metadata['Iptc.Application2.Keywords'],
                         ('test', 'photo'))
        self.assertEqual(metadata['Exif.Photo.PixelXDimension'], 1)
        self.assertEqual(metadata['Exif.Photo.PixelYDimension'], 1)

        # Synchronize only one field.
        photo.description = "Image for testing"
        photo.save()
        performed_sync = photo.sync_metadata_to_file()
        self.assertTrue(performed_sync)
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Image for testing')

        # Disable synchronization.
        photo.metadata_sync_enabled = False
        photo.description = "Sample image for testing purposes"
        photo.save()
        self.assertFalse(photo.sync_metadata_to_file())

        # Sometimes the image isn't a JPEG.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.tif')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'TIFF')
        photo = Photo()
        photo.owner = user
        photo.description = 'Test file'
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = False
        photo.save()
        image.close()
        os.remove(file_path)
        performed_sync = photo.sync_metadata_to_file()
        self.assertTrue(performed_sync)
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageWidth'], 1)
        self.assertEqual(metadata['Exif.Image.ImageLength'], 1)

        # Sometimes metadata can't be read from the image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.pcx')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'PCX')
        photo = Photo()
        photo.owner = user
        photo.description = 'Test file'
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.save()
        image.close()
        os.remove(file_path)
        self.assertFalse(photo.sync_metadata_to_file())
        self.assertFalse(photo.metadata_sync_enabled)

        # Sometimes metadata can't be written to the image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.bmp')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'BMP')
        photo = Photo()
        photo.owner = user
        photo.description = 'Test file'
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.save()
        image.close()
        os.remove(file_path)
        self.assertFalse(photo.sync_metadata_to_file())
        self.assertFalse(photo.metadata_sync_enabled)

        User.objects.all().delete()
        Album.objects.all().delete()
        PhotoTag.objects.all().delete()
        Photo.objects.all().delete()


class SyncMetadataFromFileTest(TestCase):

    def runTest(self):
        # Create an image with metadata.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        metadata['Exif.Image.ImageDescription'] = "Test file"
        metadata['Exif.Image.Artist'] = "Adam"
        metadata['Iptc.Application2.CountryName'] = "USA"
        metadata['Iptc.Application2.ProvinceState'] = "Virginia"
        metadata['Iptc.Application2.City'] = "Blacksburg"
        metadata['Iptc.Application2.SubLocation'] = "Dreamland"
        try:
            metadata['Exif.Photo.DateTimeOriginal'] = datetime.datetime(
                2007, 9, 28, 3, 0)
        except TypeError:
            pass
        metadata['Iptc.Application2.Keywords'] = ['test', 'photo']
        metadata.writeMetadata()

        # Create a Photo object.
        user = User.objects.create(username="Adam")
        album = Album.objects.create(owner=user, name="Test")
        photo = Photo()
        photo.owner = user
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.is_jpeg = True
        photo.save()
        image.close()
        os.remove(file_path)

        # Synchronize.
        performed_sync = photo.sync_metadata_from_file()
        self.assertTrue(performed_sync)

        # Metadata should exist in the database.
        self.assertEqual(photo.description, 'Test file')
        self.assertEqual(photo.artist, 'Adam')
        self.assertEqual(photo.country, 'USA')
        self.assertEqual(photo.province_state, 'Virginia')
        self.assertEqual(photo.city, 'Blacksburg')
        self.assertEqual(photo.location, 'Dreamland')
        self.assertEqual(str(photo.time_created), '2007-09-28 03:00:00')
        self.assertEqual(photo.keyword_list, [u'test', u'photo'])

        # Attempt to synchronize again...
        self.assertFalse(photo.sync_metadata_from_file())
        # Nothing should have changed.
        self.assertEqual(photo.description, 'Test file')
        self.assertEqual(photo.artist, 'Adam')
        self.assertEqual(photo.country, 'USA')
        self.assertEqual(photo.province_state, 'Virginia')
        self.assertEqual(photo.city, 'Blacksburg')
        self.assertEqual(photo.location, 'Dreamland')
        self.assertEqual(str(photo.time_created), '2007-09-28 03:00:00')
        self.assertEqual(photo.keyword_list, [u'test', u'photo'])

        # Synchronize only one field.
        metadata = pyexiv2.Image(photo.image.path)
        metadata.readMetadata()
        metadata['Exif.Image.ImageDescription'] = "Image for testing"
        metadata.writeMetadata()
        performed_sync = photo.sync_metadata_from_file()
        self.assertTrue(performed_sync)
        self.assertEqual(photo.description, 'Image for testing')

        # Disable synchronization.
        photo.metadata_sync_enabled = False
        photo.description = "Image for testing"
        photo.save()
        self.assertFalse(photo.sync_metadata_from_file())

        # Sometimes metadata can't be read from the image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.pcx')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'PCX')
        photo = Photo()
        photo.owner = user
        image = open(file_path)
        photo.image = ImageFile(image)
        photo.album = album
        photo.save()
        image.close()
        os.remove(file_path)
        self.assertFalse(photo.sync_metadata_from_file())
        self.assertFalse(photo.metadata_sync_enabled)

        User.objects.all().delete()
        Album.objects.all().delete()
        PhotoTag.objects.all().delete()
        Photo.objects.all().delete()
