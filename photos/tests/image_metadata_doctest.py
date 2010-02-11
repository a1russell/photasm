"""
>>> import datetime
>>> import os
>>> import tempfile
>>> from PIL import Image
>>> import pyexiv2
>>> from photasm.photos.image_metadata import (
...     _collapse_empty_to_none,
...     _del_img_key,
...     _is_iter,
...     _metadata_value_synced_with_file,
...     _sync_metadata_value_to_file,
...     datetime_synced_with_exif_and_iptc,
...     get_image_height_key,
...     get_image_width_key,
...     read_datetime_from_exif_and_iptc,
...     read_value_from_exif_and_iptc,
...     require_pyexiv2_obj,
...     sync_datetime_to_exif_and_iptc,
...     sync_value_to_exif,
...     sync_value_to_exif_and_iptc,
...     sync_value_to_iptc,
...     value_synced_with_exif,
...     value_synced_with_exif_and_iptc,
...     value_synced_with_iptc,
... )


>>> # Test image_metadata.get_image_width_key(img_is_jpeg)

>>> img_is_jpeg = True
>>> print get_image_width_key(img_is_jpeg)
Exif.Photo.PixelXDimension

>>> img_is_jpeg = False
>>> print get_image_width_key(img_is_jpeg)
Exif.Image.ImageWidth


>>> # Test image_metadata.get_image_height_key(img_is_jpeg)

>>> img_is_jpeg = True
>>> print get_image_height_key(img_is_jpeg)
Exif.Photo.PixelYDimension

>>> img_is_jpeg = False
>>> print get_image_height_key(img_is_jpeg)
Exif.Image.ImageLength


>>> # Test image_metadata.require_pyexiv2_obj(obj, obj_name)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)

>>> # Use this function.
>>> print require_pyexiv2_obj(metadata, 'metadata')
None
>>> test_obj = "This isn't a valid pyexiv2.Image."
>>> print require_pyexiv2_obj(test_obj, 'test_obj')
Traceback (most recent call last):
    ...
TypeError: Object 'test_obj' must be an instance of pyexiv2.Image.

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata._is_iter(obj)

>>> print _is_iter(set())
True

>>> print _is_iter("Test string.")
False

>>> print _is_iter(1)
False


>>> # Test image_metadata._collapse_empty_to_none(value)

>>> print _collapse_empty_to_none([])
None

>>> print _collapse_empty_to_none([1, 2, 3])
[1, 2, 3]

>>> print _collapse_empty_to_none(1)
1


>>> # Test image_metadata._del_img_key(image, metadata_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()

>>> # Use this function.
>>> value = 'Test file with description'
>>> metadata['Exif.Image.ImageDescription'] = value
>>> metadata.writeMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description
>>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False

>>> value = 'Test file with description'
>>> metadata['Iptc.Application2.Caption'] = value
>>> metadata.writeMetadata()
>>> _del_img_key(metadata, 'Iptc.Application2.Caption')
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False

>>> value = datetime.date.today()
>>> try:
...     metadata['Iptc.Application2.DateCreated'] = value
... except TypeError:
...     pass
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
True
>>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata._metadata_value_synced_with_file(value, image,
>>> #                                                      metadata_key,
>>> #                                                      keys_method)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> test_description = 'Test file with description'
>>> metadata['Exif.Image.ImageDescription'] = test_description
>>> metadata.writeMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description

>>> # Use this function.
>>> print _metadata_value_synced_with_file(test_description, metadata,
...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
True

>>> test_description = 'New, different test description'
>>> print _metadata_value_synced_with_file(test_description, metadata,
...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
False

>>> del metadata['Exif.Image.ImageDescription']
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> empty_string = ""
>>> print _metadata_value_synced_with_file(empty_string, metadata,
...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
True

>>> keywords = ['c', 'a', 'b']
>>> metadata['Iptc.Application2.Keywords'] = keywords
>>> metadata.writeMetadata()
>>> keywords.sort()
>>> print keywords
['a', 'b', 'c']
>>> print _metadata_value_synced_with_file(keywords, metadata,
...     'Iptc.Application2.Keywords', pyexiv2.Image.iptcKeys)
True

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.value_synced_with_exif(value, image, metadata_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> test_description = 'Test file with description'
>>> metadata['Exif.Image.ImageDescription'] = test_description
>>> metadata.writeMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description

>>> # Use this function.
>>> print value_synced_with_exif(test_description, metadata,
...                              'Exif.Image.ImageDescription')
True

>>> test_description = 'New, different test description'
>>> print value_synced_with_exif(test_description, metadata,
...                              'Exif.Image.ImageDescription')
False

>>> del metadata['Exif.Image.ImageDescription']
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> empty_string = ""
>>> print value_synced_with_exif(empty_string, metadata,
...                              'Exif.Image.ImageDescription')
True
>>> none_argument = None
>>> print value_synced_with_exif(none_argument, metadata,
...                              'Exif.Image.ImageDescription')
True

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.value_synced_with_iptc(value, image, metadata_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> test_keywords = ['IPTC', 'test', 'keywords']
>>> metadata['Iptc.Application2.Keywords'] = test_keywords
>>> metadata.writeMetadata()
>>> print metadata['Iptc.Application2.Keywords']
('IPTC', 'test', 'keywords')

>>> # Use this function.
>>> print value_synced_with_iptc(test_keywords, metadata,
...                              'Iptc.Application2.Keywords')
True

>>> test_keywords.append('modified')
>>> print value_synced_with_iptc(test_keywords, metadata,
...                              'Iptc.Application2.Keywords')
False

>>> _del_img_key(metadata, 'Iptc.Application2.Keywords')
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.Keywords' in metadata.iptcKeys()
False
>>> empty_list = []
>>> print value_synced_with_iptc(empty_list, metadata,
...                              'Iptc.Application2.Keywords')
True
>>> none_argument = None
>>> print value_synced_with_iptc(none_argument, metadata,
...                              'Iptc.Application2.Keywords')
True

>>> test_keywords = ['c', 'a', 'b']
>>> metadata['Iptc.Application2.Keywords'] = test_keywords
>>> metadata.writeMetadata()
>>> test_keywords.sort()
>>> print test_keywords
['a', 'b', 'c']
>>> print value_synced_with_iptc(test_keywords, metadata,
...                              'Iptc.Application2.Keywords')
True

>>> empty_string = ""
>>> print value_synced_with_iptc(empty_string, metadata,
...                              'Iptc.Application2.Caption')
True

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.value_synced_with_exif_and_iptc(value, image,
>>> #                                                     exif_key, iptc_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> test_description = 'Test file with description'
>>> metadata['Exif.Image.ImageDescription'] = test_description
>>> metadata['Iptc.Application2.Caption'] = test_description
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description
>>> print metadata['Iptc.Application2.Caption']
Test file with description

>>> # Use this function.
>>> print value_synced_with_exif_and_iptc(test_description, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
True

>>> test_description = 'New, different test description'
>>> print value_synced_with_exif_and_iptc(test_description, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
False

>>> test_description = metadata['Exif.Image.ImageDescription']
>>> metadata['Exif.Image.ImageDescription'] = 'modified'
>>> metadata.writeMetadata()
>>> print value_synced_with_exif_and_iptc(test_description, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
False

>>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> print value_synced_with_exif_and_iptc(test_description, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
True

>>> _del_img_key(metadata, 'Iptc.Application2.Caption')
>>> metadata['Exif.Image.ImageDescription'] = test_description
>>> metadata.writeMetadata()
>>> print value_synced_with_exif_and_iptc(test_description, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
True

>>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False
>>> empty_string = ""
>>> print value_synced_with_exif_and_iptc(empty_string, metadata,
...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
True

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.datetime_synced_with_exif_and_iptc(
>>> #     datetime_value, image, exif_datetime_key,
>>> #     iptc_date_key, iptc_time_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> value = datetime.datetime.now()
>>> time_keys = ('Exif.Photo.DateTimeOriginal',
...              'Iptc.Application2.DateCreated',
...              'Iptc.Application2.TimeCreated',)
>>> metadata['Exif.Photo.DateTimeOriginal'] = value
>>> try:
...     metadata['Iptc.Application2.DateCreated'] = value.date()
... except TypeError:
...     pass
>>> try:
...     metadata['Iptc.Application2.TimeCreated'] = value.time()
... except TypeError:
...     pass
>>> metadata.writeMetadata()

>>> # Use this function.
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
True

>>> one_second = datetime.timedelta(seconds=1)
>>> value = value + one_second
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
False

>>> value = metadata['Exif.Photo.DateTimeOriginal']
>>> metadata['Exif.Photo.DateTimeOriginal'] =  value + one_second
>>> metadata.writeMetadata()
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
False

>>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
>>> metadata.writeMetadata()
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
True

>>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
>>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
>>> metadata['Exif.Photo.DateTimeOriginal'] = value
>>> metadata.writeMetadata()
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
True

>>> value = None
>>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
>>> metadata.writeMetadata()
>>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
True

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata._sync_metadata_value_to_file(value, image,
>>> #                                                  metadata_key,
>>> #                                                  sync_check_func)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()

>>> # Use this function.
>>> test_description = 'Test file with description'
>>> print _sync_metadata_value_to_file(test_description, metadata,
...     'Exif.Image.ImageDescription', value_synced_with_exif)
True
>>> metadata.writeMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description
>>> print _sync_metadata_value_to_file(test_description, metadata,
...     'Exif.Image.ImageDescription', value_synced_with_exif)
False

>>> empty_string = ''
>>> print _sync_metadata_value_to_file(empty_string, metadata,
...     'Exif.Image.ImageDescription', value_synced_with_exif)
True
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> print _sync_metadata_value_to_file(empty_string, metadata,
...     'Exif.Image.ImageDescription', value_synced_with_exif)
False

>>> none_argument = None
>>> print 'Exif.Image.Orientation' in metadata.exifKeys()
False
>>> print _sync_metadata_value_to_file(none_argument, metadata,
...     'Exif.Image.Orientation', value_synced_with_exif)
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.sync_value_to_exif(value, image, metadata_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()

>>> # Use this function.
>>> test_description = 'Test file with description'
>>> print sync_value_to_exif(test_description, metadata,
...                          'Exif.Image.ImageDescription')
True
>>> metadata.writeMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description
>>> print sync_value_to_exif(test_description, metadata,
...                          'Exif.Image.ImageDescription')
False

>>> empty_string = ''
>>> print sync_value_to_exif(empty_string, metadata,
...                          'Exif.Image.ImageDescription')
True
>>> metadata.writeMetadata()
>>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
False
>>> print sync_value_to_exif(empty_string, metadata,
...                          'Exif.Image.ImageDescription')
False

>>> none_argument = None
>>> print 'Exif.Image.Orientation' in metadata.exifKeys()
False
>>> print sync_value_to_exif(none_argument, metadata,
...                          'Exif.Image.Orientation')
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.sync_value_to_iptc(value, image, metadata_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()

>>> # Use this function.
>>> test_description = 'Test file with description'
>>> print sync_value_to_iptc(test_description, metadata,
...                          'Iptc.Application2.Caption')
True
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print metadata['Iptc.Application2.Caption']
Test file with description
>>> print sync_value_to_iptc(test_description, metadata,
...                          'Iptc.Application2.Caption')
False

>>> empty_string = ""
>>> print sync_value_to_iptc(empty_string, metadata,
...                          'Iptc.Application2.Caption')
True
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False
>>> print sync_value_to_iptc(empty_string, metadata,
...                          'Iptc.Application2.Caption')
False

>>> test_keywords = ['IPTC', 'test', 'keywords']
>>> print sync_value_to_iptc(test_keywords, metadata,
...                          'Iptc.Application2.Keywords')
True
>>> metadata.writeMetadata()
>>> print metadata['Iptc.Application2.Keywords']
('IPTC', 'test', 'keywords')

>>> empty_list = []
>>> print sync_value_to_iptc(empty_list, metadata,
...                          'Iptc.Application2.Keywords')
True
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.Keywords' in metadata.iptcKeys()
False
>>> print sync_value_to_iptc(empty_list, metadata,
...                          'Iptc.Application2.Keywords')
False

>>> none_argument = None
>>> print 'Iptc.Envelope.ARMId' in metadata.iptcKeys()
False
>>> print sync_value_to_iptc(none_argument, metadata,
...                          'Iptc.Application2.DateCreated')
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.sync_value_to_exif_and_iptc(value, image, exif_key,
>>> #                                                 iptc_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')

>>> # Use this function.
>>> test_description = 'Test file with description'
>>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file with description
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False
>>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
False
>>> metadata['Iptc.Application2.Caption'] = test_description
>>> del metadata['Exif.Image.ImageDescription']
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
False

>>> test_description = 'File with NEW description'
>>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
File with NEW description
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False

>>> empty_string = ""
>>> print sync_value_to_exif_and_iptc(empty_string, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
False
>>> print sync_value_to_exif_and_iptc(empty_string, metadata, *keys)
False

>>> none_argument = None
>>> print sync_value_to_exif_and_iptc(none_argument, metadata, *keys)
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.sync_datetime_to_exif_and_iptc(
>>> #     datetime_value, image, exif_datetime_key,
>>> #     iptc_date_key, iptc_time_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> keys = ('Exif.Photo.DateTimeOriginal',
...         'Iptc.Application2.DateCreated',
...         'Iptc.Application2.TimeCreated',)

>>> # Use this function.
>>> value = datetime.datetime.now()
>>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> # Metadata doesn't have microsecond precision.
>>> value_no_us = value.replace(microsecond=0)
>>> print metadata['Exif.Photo.DateTimeOriginal'] == value_no_us
True
>>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
False
>>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
False
>>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
False
>>> try:
...     metadata['Iptc.Application2.DateCreated'] = value.date()
... except TypeError:
...     pass
>>> try:
...     metadata['Iptc.Application2.TimeCreated'] = value.time()
... except TypeError:
...     pass
>>> del metadata['Exif.Photo.DateTimeOriginal']
>>> metadata.writeMetadata()
>>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
False

>>> one_second = datetime.timedelta(seconds=1)
>>> value += one_second
>>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> value_no_us = value.replace(microsecond=0)
>>> print metadata['Exif.Photo.DateTimeOriginal'] == value_no_us
True
>>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
False
>>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
False

>>> none_argument = None
>>> print sync_datetime_to_exif_and_iptc(none_argument, metadata, *keys)
True
>>> metadata.writeMetadata()
>>> print 'Exif.Photo.DateTimeOriginal' in metadata.exifKeys()
False
>>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
False
>>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
False
>>> print sync_datetime_to_exif_and_iptc(none_argument, metadata, *keys)
False

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.read_value_from_exif_and_iptc(image, exif_key,
>>> #                                                   iptc_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
>>> exif_val = 'Test file with Exif description tag'
>>> iptc_val = 'Test file with IPTC description tag'

>>> # Use this function
>>> metadata['Exif.Image.ImageDescription'] = exif_val
>>> metadata['Iptc.Application2.Caption'] = iptc_val
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print read_value_from_exif_and_iptc(metadata, *keys) == exif_val
True

>>> _del_img_key(metadata, 'Iptc.Application2.Caption')
>>> metadata.writeMetadata()
>>> print read_value_from_exif_and_iptc(metadata, *keys) == exif_val
True

>>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
>>> metadata['Iptc.Application2.Caption'] = iptc_val
>>> metadata.writeMetadata()
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> print read_value_from_exif_and_iptc(metadata, *keys) == iptc_val
True

>>> _del_img_key(metadata, 'Iptc.Application2.Caption')
>>> metadata.writeMetadata()
>>> print read_value_from_exif_and_iptc(metadata, *keys)
None

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test image_metadata.read_datetime_from_exif_and_iptc(
>>> #     image, exif_datetime_key, iptc_date_key, iptc_time_key)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> keys = ('Exif.Photo.DateTimeOriginal',
...         'Iptc.Application2.DateCreated',
...         'Iptc.Application2.TimeCreated',)
>>> # Note that metadata doesn't have microsecond precision.
>>> exif_val = datetime.datetime(2007, 9, 28, 3, 0)
>>> iptc_val = datetime.datetime(2007, 10, 10, 5, 0)
>>> iptc_date = iptc_val.date()
>>> iptc_time = iptc_val.time()

>>> # Use this function
>>> metadata['Exif.Photo.DateTimeOriginal'] = exif_val
>>> try:
...     metadata['Iptc.Application2.DateCreated'] = iptc_date
... except TypeError:
...     pass
>>> try:
...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
... except TypeError:
...     pass
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys) == exif_val
True

>>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
>>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys) == exif_val
True

>>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
>>> try:
...     metadata['Iptc.Application2.DateCreated'] = iptc_date
... except TypeError:
...     pass
>>> try:
...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
... except TypeError:
...     pass
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys) == iptc_val
True

>>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
>>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys)
None

>>> try:
...     metadata['Iptc.Application2.DateCreated'] = iptc_date
... except TypeError:
...     pass
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys)
None

>>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
>>> try:
...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
... except TypeError:
...     pass
>>> metadata.writeMetadata()
>>> print read_datetime_from_exif_and_iptc(metadata, *keys)
None

>>> # Clean up.
>>> os.remove(file_path)

"""

