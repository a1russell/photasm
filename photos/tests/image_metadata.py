import datetime
import os
import tempfile

from django.test import TestCase
from PIL import Image
import pyexiv2

from photasm.photos.image_metadata import (
    _collapse_iter,
    _del_img_key,
    _is_iter,
    datetime_synced_with_exif_and_iptc,
    get_image_height_key,
    get_image_width_key,
    read_datetime_from_exif_and_iptc,
    read_value_from_exif_and_iptc,
    require_pyexiv2_obj,
    sync_datetime_to_exif_and_iptc,
    sync_value_to_exif,
    sync_value_to_exif_and_iptc,
    sync_value_to_iptc,
    value_synced_with_exif,
    value_synced_with_exif_and_iptc,
    value_synced_with_iptc,
)


class ImageMetadataTest(TestCase):

    def test_get_image_width_key(self):
        img_is_jpeg = True
        self.assertEqual(get_image_width_key(img_is_jpeg),
                         'Exif.Photo.PixelXDimension')

        img_is_jpeg = False
        self.assertEqual(get_image_width_key(img_is_jpeg),
                         'Exif.Image.ImageWidth')

    def test_get_image_height_key(self):
        img_is_jpeg = True
        self.assertEqual(get_image_height_key(img_is_jpeg),
                         'Exif.Photo.PixelYDimension')

        img_is_jpeg = False
        self.assertEqual(get_image_height_key(img_is_jpeg),
                         'Exif.Image.ImageLength')

    def test_require_pyexiv2_obj(self):
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)

        self.assertEqual(require_pyexiv2_obj(metadata, 'metadata'), None)
        test_obj = "This isn't a valid pyexiv2.Image."
        self.assertRaises(TypeError, require_pyexiv2_obj, test_obj, 'test_obj')

        os.remove(file_path)

    def test_is_iter(self):
        self.assertTrue(_is_iter(set()))
        self.assertFalse(_is_iter("Test string."))
        self.assertFalse(_is_iter(u"Test string."))
        self.assertFalse(_is_iter(1))

    def test_collapse_iter(self):
        self.assertEqual(_collapse_iter([]), None)
        self.assertEqual(_collapse_iter([1, 2, 3]), [1, 2, 3])
        self.assertEqual(_collapse_iter(1), 1)
        self.assertEqual(_collapse_iter((1,)), 1)
        self.assertEqual(_collapse_iter(set([1])), 1)

    def test_del_img_key(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        # Add and delete Exif metadata.
        value = 'Test file with description'
        metadata['Exif.Image.ImageDescription'] = value
        metadata.writeMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Test file with description')
        _del_img_key(metadata, 'Exif.Image.ImageDescription')
        metadata.writeMetadata()
        self.assertFalse('Exif.Image.ImageDescription' in metadata.exifKeys())

        # Add and delete IPTC string metadata.
        value = 'Test file with description'
        metadata['Iptc.Application2.Caption'] = value
        metadata.writeMetadata()
        _del_img_key(metadata, 'Iptc.Application2.Caption')
        metadata.writeMetadata()
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())

        # Add and delete IPTC date metadata.
        value = datetime.date.today()
        try:
            metadata['Iptc.Application2.DateCreated'] = value
        except TypeError:
            pass
        metadata.writeMetadata()
        self.assertTrue(
            'Iptc.Application2.DateCreated' in metadata.iptcKeys())
        _del_img_key(metadata, 'Iptc.Application2.DateCreated')
        metadata.writeMetadata()
        self.assertFalse(
            'Iptc.Application2.DateCreated' in metadata.iptcKeys())

        os.remove(file_path)

    def test_value_synced_with_exif(self):
        # Create an image with metadata.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        test_description = 'Test file with description'
        metadata['Exif.Image.ImageDescription'] = test_description
        metadata.writeMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Test file with description')

        # Test synchronization status.
        self.assertTrue(value_synced_with_exif(test_description, metadata,
                                                'Exif.Image.ImageDescription'))
        test_description = 'New, different test description'
        self.assertFalse(value_synced_with_exif(test_description, metadata,
                                                'Exif.Image.ImageDescription'))

        # Test synchronization of nonexistent/empty metadata.
        del metadata['Exif.Image.ImageDescription']
        metadata.writeMetadata()
        self.assertFalse('Exif.Image.ImageDescription' in metadata.exifKeys())
        empty_string = ""
        self.assertTrue(value_synced_with_exif(empty_string, metadata,
                                                'Exif.Image.ImageDescription'))
        none_argument = None
        self.assertTrue(value_synced_with_exif(none_argument, metadata,
                                                'Exif.Image.ImageDescription'))

        # Clean up.
        os.remove(file_path)

    def test_value_synced_with_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        # Add string metadata.
        test_description = 'Test file with description'
        metadata['Iptc.Application2.Caption'] = test_description
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(metadata['Iptc.Application2.Caption'],
                         'Test file with description')

        # Test synchronization status of string metadata.
        self.assertTrue(value_synced_with_iptc(test_description, metadata,
                                                'Iptc.Application2.Caption'))
        test_description = 'New, different test description'
        self.assertFalse(value_synced_with_iptc(test_description, metadata,
                                                'Iptc.Application2.Caption'))

        # Add iterable metadata.
        test_keywords = ['IPTC', 'test', 'keywords']
        metadata['Iptc.Application2.Keywords'] = test_keywords
        metadata.writeMetadata()
        self.assertEqual(metadata['Iptc.Application2.Keywords'],
                         ('IPTC', 'test', 'keywords'))

        # Test synchronization status of iterable metadata.
        self.assertTrue(value_synced_with_iptc(test_keywords, metadata,
                                                'Iptc.Application2.Keywords'))
        test_keywords.append('modified')
        self.assertFalse(value_synced_with_iptc(test_keywords, metadata,
                                                'Iptc.Application2.Keywords'))

        # Test synchronization of nonexistent/empty iterable metadata.
        _del_img_key(metadata, 'Iptc.Application2.Keywords')
        metadata.writeMetadata()
        self.assertFalse('Iptc.Application2.Keywords' in metadata.iptcKeys())
        empty_list = []
        self.assertTrue(value_synced_with_iptc(empty_list, metadata,
                                                'Iptc.Application2.Keywords'))
        none_argument = None
        self.assertTrue(value_synced_with_iptc(none_argument, metadata,
                                                'Iptc.Application2.Keywords'))

        # Test synchronization of iterables that are sorted differently.
        test_keywords = ['c', 'a', 'b']
        metadata['Iptc.Application2.Keywords'] = test_keywords
        metadata.writeMetadata()
        test_keywords.sort()
        self.assertEqual(test_keywords, ['a', 'b', 'c'])
        self.assertTrue(value_synced_with_iptc(test_keywords, metadata,
                                                'Iptc.Application2.Keywords'))

        # Test synchronization of iterables of length one.
        test_keywords = ['a']
        try:
            metadata['Iptc.Application2.Keywords'] = test_keywords
        except TypeError:
            pass
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertTrue(value_synced_with_iptc(test_keywords, metadata,
                                                'Iptc.Application2.Keywords'))

        # Test synchronization of empty/nonexistent string metadata.
        empty_string = ""
        _del_img_key(metadata, 'Iptc.Application2.Caption')
        self.assertTrue(value_synced_with_iptc(empty_string, metadata,
                                                'Iptc.Application2.Caption'))

        # Clean up.
        os.remove(file_path)

    def test_value_synced_with_exif_and_iptc(self):
        # Create an image with metadata.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        test_description = 'Test file with description'
        metadata['Exif.Image.ImageDescription'] = test_description
        metadata['Iptc.Application2.Caption'] = test_description
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Test file with description')
        self.assertEqual(metadata['Iptc.Application2.Caption'],
                         'Test file with description')

        # Test synchronization status.
        self.assertTrue(
            value_synced_with_exif_and_iptc(test_description, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        test_description = 'New, different test description'
        self.assertFalse(
            value_synced_with_exif_and_iptc(test_description, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        test_description = metadata['Exif.Image.ImageDescription']
        metadata['Exif.Image.ImageDescription'] = 'modified'
        metadata.writeMetadata()
        self.assertFalse(
            value_synced_with_exif_and_iptc(test_description, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        _del_img_key(metadata, 'Exif.Image.ImageDescription')
        metadata.writeMetadata()
        self.assertFalse('Exif.Image.ImageDescription' in metadata.exifKeys())
        self.assertTrue(
            value_synced_with_exif_and_iptc(test_description, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        _del_img_key(metadata, 'Iptc.Application2.Caption')
        metadata['Exif.Image.ImageDescription'] = test_description
        metadata.writeMetadata()
        self.assertTrue(
            value_synced_with_exif_and_iptc(test_description, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        _del_img_key(metadata, 'Exif.Image.ImageDescription')
        metadata.writeMetadata()
        self.assertFalse('Exif.Image.ImageDescription' in metadata.exifKeys())
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())
        empty_string = ""
        self.assertTrue(
            value_synced_with_exif_and_iptc(empty_string, metadata,
                                            'Exif.Image.ImageDescription',
                                            'Iptc.Application2.Caption'))

        # Clean up.
        os.remove(file_path)

    def test_datetime_synced_with_exif_and_iptc(self):
        # Create an image with metadata.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        value = datetime.datetime.now()
        time_keys = ('Exif.Photo.DateTimeOriginal',
                     'Iptc.Application2.DateCreated',
                     'Iptc.Application2.TimeCreated',)
        metadata['Exif.Photo.DateTimeOriginal'] = value
        try:
            metadata['Iptc.Application2.DateCreated'] = value.date()
        except TypeError:
            pass
        try:
            metadata['Iptc.Application2.TimeCreated'] = value.time()
        except TypeError:
            pass
        metadata.writeMetadata()

        # Test synchronization status.
        self.assertTrue(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        one_second = datetime.timedelta(seconds=1)
        value = value + one_second
        self.assertFalse(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        value = metadata['Exif.Photo.DateTimeOriginal']
        metadata['Exif.Photo.DateTimeOriginal'] = value + one_second
        metadata.writeMetadata()
        self.assertFalse(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
        metadata.writeMetadata()
        self.assertTrue(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        _del_img_key(metadata, 'Iptc.Application2.DateCreated')
        _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
        metadata['Exif.Photo.DateTimeOriginal'] = value
        metadata.writeMetadata()
        self.assertTrue(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        value = None
        _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
        metadata.writeMetadata()
        self.assertTrue(
            datetime_synced_with_exif_and_iptc(value, metadata, *time_keys))

        # Clean up.
        os.remove(file_path)

    def test_sync_value_to_exif(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        # Synchronize a string.
        test_description = 'Test file with description'
        performed_sync = sync_value_to_exif(test_description, metadata,
                                            'Exif.Image.ImageDescription')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Test file with description')
        self.assertFalse(sync_value_to_exif(test_description, metadata,
                                            'Exif.Image.ImageDescription'))

        # Synchronize an empty string.
        empty_string = ''
        performed_sync = sync_value_to_exif(empty_string, metadata,
                                            'Exif.Image.ImageDescription')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertFalse('Exif.Image.ImageDescription' in metadata.exifKeys())
        self.assertFalse(sync_value_to_exif(empty_string, metadata,
                                            'Exif.Image.ImageDescription'))

        # Synchronizing the None value has the same effect as an empty string.
        none_argument = None
        self.assertFalse('Exif.Image.Orientation' in metadata.exifKeys())
        self.assertFalse(sync_value_to_exif(none_argument, metadata,
                                            'Exif.Image.Orientation'))

        # Clean up.
        os.remove(file_path)

    def test_sync_value_to_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        # Synchronize a string.
        test_description = 'Test file with description'
        performed_sync = sync_value_to_iptc(test_description, metadata,
                                            'Iptc.Application2.Caption')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(metadata['Iptc.Application2.Caption'],
                         'Test file with description')
        self.assertFalse(sync_value_to_iptc(test_description, metadata,
                                            'Iptc.Application2.Caption'))

        # Synchronize an empty string.
        empty_string = ""
        performed_sync = sync_value_to_iptc(empty_string, metadata,
                                            'Iptc.Application2.Caption')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())
        self.assertFalse(sync_value_to_iptc(empty_string, metadata,
                                            'Iptc.Application2.Caption'))

        # Synchronize an iterable.
        test_keywords = ['IPTC', 'test', 'keywords']
        performed_sync = sync_value_to_iptc(test_keywords, metadata,
                                            'Iptc.Application2.Keywords')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertEqual(metadata['Iptc.Application2.Keywords'],
                         ('IPTC', 'test', 'keywords'))

        # Synchronize an empty iterable.
        empty_list = []
        performed_sync = sync_value_to_iptc(empty_list, metadata,
                                            'Iptc.Application2.Keywords')
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertFalse('Iptc.Application2.Keywords' in metadata.iptcKeys())
        self.assertFalse(sync_value_to_iptc(empty_list, metadata,
                                            'Iptc.Application2.Keywords'))

        # Syncing the None value has the same effect as an empty one.
        none_argument = None
        self.assertFalse('Iptc.Envelope.ARMId' in metadata.iptcKeys())
        self.assertFalse(sync_value_to_iptc(none_argument, metadata,
                                            'Iptc.Application2.DateCreated'))

        # Clean up.
        os.remove(file_path)

    def test_sync_value_to_exif_and_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')

        # Synchronize to Exif.
        test_description = 'Test file with description'
        performed_sync = sync_value_to_exif_and_iptc(test_description,
                                                     metadata, *keys)
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'Test file with description')
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())
        self.assertFalse(
            sync_value_to_exif_and_iptc(test_description, metadata, *keys))
        metadata['Iptc.Application2.Caption'] = test_description

        # If the value exists in IPTC, the metadata isn't modified.
        del metadata['Exif.Image.ImageDescription']
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertFalse(
            sync_value_to_exif_and_iptc(test_description, metadata, *keys))

        # Syncing a new value will remove the IPTC in favor of Exif.
        test_description = 'File with NEW description'
        performed_sync = sync_value_to_exif_and_iptc(test_description,
                                                     metadata, *keys)
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(metadata['Exif.Image.ImageDescription'],
                         'File with NEW description')
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())

        # Synchronize an empty string.
        empty_string = ""
        performed_sync = sync_value_to_exif_and_iptc(empty_string,
                                                     metadata, *keys),
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertFalse('Iptc.Application2.Caption' in metadata.iptcKeys())
        self.assertFalse(
            sync_value_to_exif_and_iptc(empty_string, metadata, *keys))

        # Syncig the None value has the same effect as an empty one.
        none_argument = None
        self.assertFalse(
            sync_value_to_exif_and_iptc(none_argument, metadata, *keys))

        # Clean up.
        os.remove(file_path)

    def test_sync_datetime_to_exif_and_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        keys = ('Exif.Photo.DateTimeOriginal',
                'Iptc.Application2.DateCreated',
                'Iptc.Application2.TimeCreated',)

        # Synchronize to Exif.
        value = datetime.datetime.now()
        performed_sync = sync_datetime_to_exif_and_iptc(value, metadata,
                                                        *keys)
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        # Metadata doesn't have microsecond precision.
        value_no_us = value.replace(microsecond=0)
        self.assertEqual(metadata['Exif.Photo.DateTimeOriginal'], value_no_us)
        self.assertFalse(
            'Iptc.Application2.DateCreated' in metadata.iptcKeys())
        self.assertFalse(
            'Iptc.Application2.TimeCreated' in metadata.iptcKeys())
        self.assertFalse(
            sync_datetime_to_exif_and_iptc(value, metadata, *keys))
        try:
            metadata['Iptc.Application2.DateCreated'] = value.date()
        except TypeError:
            pass
        try:
            metadata['Iptc.Application2.TimeCreated'] = value.time()
        except TypeError:
            pass

        # If the value exists in IPTC, the metadata isn't modified.
        del metadata['Exif.Photo.DateTimeOriginal']
        metadata.writeMetadata()
        self.assertFalse(
            sync_datetime_to_exif_and_iptc(value, metadata, *keys))

        # Syncing a new value will remove the IPTC in favor of Exif.
        one_second = datetime.timedelta(seconds=1)
        value += one_second
        performed_sync = sync_datetime_to_exif_and_iptc(value, metadata,
                                                        *keys)
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        value_no_us = value.replace(microsecond=0)
        self.assertEqual(metadata['Exif.Photo.DateTimeOriginal'], value_no_us)
        self.assertFalse(
            'Iptc.Application2.DateCreated' in metadata.iptcKeys())
        self.assertFalse(
            'Iptc.Application2.TimeCreated' in metadata.iptcKeys())

        # Synchronize the None value.
        none_argument = None
        performed_sync = sync_datetime_to_exif_and_iptc(none_argument,
                                                        metadata, *keys)
        self.assertTrue(performed_sync)
        metadata.writeMetadata()
        self.assertFalse(
            'Exif.Photo.DateTimeOriginal' in metadata.exifKeys())
        self.assertFalse(
            'Iptc.Application2.DateCreated' in metadata.iptcKeys())
        self.assertFalse(
            'Iptc.Application2.TimeCreated' in metadata.iptcKeys())
        self.assertFalse(
            sync_datetime_to_exif_and_iptc(none_argument, metadata, *keys))

        # Clean up.
        os.remove(file_path)

    def test_read_value_from_exif_and_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
        exif_val = 'Test file with Exif description tag'
        iptc_val = 'Test file with IPTC description tag'

        # Read metadata from image after conflicting Exif and IPTC
        # have been added to the image. Exif should be preferred.
        metadata['Exif.Image.ImageDescription'] = exif_val
        metadata['Iptc.Application2.Caption'] = iptc_val
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(read_value_from_exif_and_iptc(metadata, *keys),
                         exif_val)

        # Read metadata value when image contains only Exif.
        _del_img_key(metadata, 'Iptc.Application2.Caption')
        metadata.writeMetadata()
        self.assertEqual(read_value_from_exif_and_iptc(metadata, *keys),
                         exif_val)

        # Read metadata value when image contains only IPTC.
        _del_img_key(metadata, 'Exif.Image.ImageDescription')
        metadata['Iptc.Application2.Caption'] = iptc_val
        metadata.writeMetadata()
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()
        self.assertEqual(read_value_from_exif_and_iptc(metadata, *keys),
                         iptc_val)

        # Attempt to read nonexistent metadata.
        _del_img_key(metadata, 'Iptc.Application2.Caption')
        metadata.writeMetadata()
        self.assertEqual(read_value_from_exif_and_iptc(metadata, *keys), None)

        # Clean up.
        os.remove(file_path)

    def test_read_datetime_from_exif_and_iptc(self):
        # Create an image.
        file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        os.close(file_descriptor)
        Image.new('RGB', (1, 1)).save(file_path, 'JPEG')
        metadata = pyexiv2.Image(file_path)
        metadata.readMetadata()

        keys = ('Exif.Photo.DateTimeOriginal',
                'Iptc.Application2.DateCreated',
                'Iptc.Application2.TimeCreated',)
        # Note that metadata doesn't have microsecond precision.
        exif_val = datetime.datetime(2007, 9, 28, 3, 0)
        iptc_val = datetime.datetime(2007, 10, 10, 5, 0)
        iptc_date = iptc_val.date()
        iptc_time = iptc_val.time()

        # Read metadata from image after conflicting Exif and IPTC
        # have been added to the image. Exif should be preferred.
        metadata['Exif.Photo.DateTimeOriginal'] = exif_val
        try:
            metadata['Iptc.Application2.DateCreated'] = iptc_date
        except TypeError:
            pass
        try:
            metadata['Iptc.Application2.TimeCreated'] = iptc_time
        except TypeError:
            pass
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
                         exif_val)

        # Read metadata value when image contains only Exif.
        _del_img_key(metadata, 'Iptc.Application2.DateCreated')
        _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
                         exif_val)

        # Read metadata value when image contains only IPTC.
        _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
        try:
            metadata['Iptc.Application2.DateCreated'] = iptc_date
        except TypeError:
            pass
        try:
            metadata['Iptc.Application2.TimeCreated'] = iptc_time
        except TypeError:
            pass
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
                         iptc_val)

        # Attempt to read nonexistent metadata.
        _del_img_key(metadata, 'Iptc.Application2.DateCreated')
        _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
            None)

        # Attempt to read incomplete metadata containing only IPTC date.
        try:
            metadata['Iptc.Application2.DateCreated'] = iptc_date
        except TypeError:
            pass
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
            None)

        # Attempt to read incomplete metadata containing only IPTC time.
        _del_img_key(metadata, 'Iptc.Application2.DateCreated')
        try:
            metadata['Iptc.Application2.TimeCreated'] = iptc_time
        except TypeError:
            pass
        metadata.writeMetadata()
        self.assertEqual(read_datetime_from_exif_and_iptc(metadata, *keys),
                         None)

        # Clean up.
        os.remove(file_path)
