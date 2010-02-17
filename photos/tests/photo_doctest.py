"""
>>> import datetime
>>> import os
>>> import tempfile
>>> from django.contrib.auth.models import User
>>> from django.core.files.images import ImageFile
>>> from PIL import Image
>>> import pyexiv2
>>> from photasm.photos.models import Album, Photo, PhotoTag


>>> # Test Photo.get_keywords()

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> User.objects.all().delete()

>>> # Create some models.
>>> photo = Photo()
>>> owner = User.objects.create(username='Adam')
>>> album = Album.objects.create(name='test', owner=owner)
>>> test_kw = PhotoTag.objects.create(name="test")
>>> photo_kw = PhotoTag.objects.create(name="photo")
>>> photo.owner = owner
>>> photo.album = album
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.save()
>>> image.close()

>>> # Use this function
>>> print photo.get_keywords()
[]

>>> photo.keywords.add(test_kw)
>>> photo.keywords.add(photo_kw)
>>> photo.save()
>>> print photo.get_keywords()
[u'test', u'photo']

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test Photo.set_keywords(keywords)

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> User.objects.all().delete()
>>> PhotoTag.objects.all().delete()

>>> # Create some models.
>>> test_kw = PhotoTag.objects.create(name="test")
>>> photo = Photo()
>>> owner = User.objects.create(username='Adam')
>>> album = Album.objects.create(name='test', owner=owner)
>>> photo.owner = owner
>>> photo.album = album
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.save()
>>> image.close()
>>> print photo.get_keywords()
[]
>>> print test_kw.photo_set.count()
0
>>> print PhotoTag.objects.count()
1

>>> # Use this function
>>> photo.set_keywords(['Test', 'photo'])
>>> photo.save()
>>> print photo.get_keywords()
[u'test', u'photo']
>>> print test_kw.photo_set.count()
1
>>> print PhotoTag.objects.count()
2

>>> photo.set_keywords(['foo', 'bar'])
>>> photo.save()
>>> print photo.get_keywords()
[u'foo', u'bar']
>>> print test_kw.photo_set.count()
0
>>> print PhotoTag.objects.count()
4

>>> photo.set_keywords([])
>>> photo.save()
>>> print photo.get_keywords()
[]

>>> # Clean up.
>>> os.remove(file_path)


>>> # Test Photo.create_thumbnail()

>>> # Create a JPEG with an embedded thumbnail.
>>> image_fd, image_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(image_fd)
>>> thumb_fd, thumb_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(thumb_fd)
>>> image = Image.new('RGB', (640, 480))
>>> image.save(image_path, 'JPEG')
>>> thumb = image.copy()
>>> thumb.thumbnail((160, 120))
>>> thumb.save(thumb_path, 'JPEG')
>>> # Write the thumbnail to the image metadata.
>>> metadata = pyexiv2.Image(image_path)
>>> metadata.readMetadata()
>>> metadata.setThumbnailFromJpegFile(thumb_path)
>>> metadata.writeMetadata()
>>> os.remove(thumb_path)
>>> User.objects.all().delete()
>>> # Create Photo model object.
>>> user = User.objects.create(username="Adam")
>>> album = Album.objects.create(owner=user, name="Test")
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(image_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = True
>>> photo.save()
>>> image.close()
>>> os.remove(image_path)

>>> # Create and verify the thumbnail.
>>> photo.create_thumbnail()
>>> photo.save()
>>> thumb = Image.open(photo.thumbnail.path)
>>> print thumb.size[0] * thumb.size[1]
19200
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> embedded = metadata.getThumbnailData()[1]
>>> external = open(photo.thumbnail.path).read()
>>> embedded == external
True

>>> # Test JPEG without thumbnail already embedded.
>>> image = Image.new('RGB', (640, 480))
>>> image.save(image_path, 'JPEG')
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(image_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = True
>>> photo.save()
>>> image.close()
>>> os.remove(image_path)
>>> photo.create_thumbnail()
>>> photo.save()
>>> thumb = Image.open(photo.thumbnail.path)
>>> print thumb.size[0] * thumb.size[1]
19200
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> embedded = metadata.getThumbnailData()[1]
>>> external = open(photo.thumbnail.path).read()
>>> print embedded == external
True

>>> # Test BMP.
>>> image_fd, image_path = tempfile.mkstemp(suffix='.bmp')
>>> os.close(image_fd)
>>> image = Image.new('RGB', (640, 480))
>>> image.save(image_path, 'BMP')
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(image_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = False
>>> photo.save()
>>> image.close()
>>> os.remove(image_path)
>>> photo.create_thumbnail()
>>> photo.save()
>>> thumb = Image.open(photo.thumbnail.path)
>>> print thumb.size[0] * thumb.size[1]
19200

>>> # Test small image.
>>> image = Image.new('RGB', (80, 60))
>>> image.save(image_path, 'JPEG')
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(image_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = True
>>> photo.save()
>>> image.close()
>>> os.remove(image_path)
>>> print photo.create_thumbnail()
None
>>> photo.save()
>>> thumb = Image.open(photo.thumbnail.path)
>>> print thumb.size
(80, 60)
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> embedded = metadata.getThumbnailData()[1]
>>> external = open(photo.thumbnail.path).read()
>>> print embedded == external
True


>>> # Test Photo.sync_metadata_to_file()

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> User.objects.all().delete()

>>> user = User.objects.create(username="Adam")
>>> album = Album.objects.create(owner=user, name="Test")
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.description = "Test file"
>>> photo.artist = "Adam"
>>> photo.country = "USA"
>>> photo.province_state = "Virginia"
>>> photo.city = "Blacksburg"
>>> photo.location = "Dreamland"
>>> photo.time_created = datetime.datetime(2007, 9, 28, 3, 0)
>>> photo.album = album
>>> photo.is_jpeg = True
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> photo.set_keywords(['test', 'photo'])
>>> photo.save()
>>> photo.sync_metadata_to_file()
True

>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file
>>> print metadata['Exif.Image.Artist']
Adam
>>> print metadata['Iptc.Application2.CountryName']
USA
>>> print metadata['Iptc.Application2.ProvinceState']
Virginia
>>> print metadata['Iptc.Application2.City']
Blacksburg
>>> print metadata['Iptc.Application2.SubLocation']
Dreamland
>>> print metadata['Exif.Photo.DateTimeOriginal']
2007-09-28 03:00:00
>>> print metadata['Iptc.Application2.Keywords']
('test', 'photo')
>>> print metadata['Exif.Photo.PixelXDimension']
1
>>> print metadata['Exif.Photo.PixelYDimension']
1

>>> photo.sync_metadata_to_file()
False
>>> # Nothing should have changed.
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Test file
>>> print metadata['Exif.Image.Artist']
Adam
>>> print metadata['Iptc.Application2.CountryName']
USA
>>> print metadata['Iptc.Application2.ProvinceState']
Virginia
>>> print metadata['Iptc.Application2.City']
Blacksburg
>>> print metadata['Iptc.Application2.SubLocation']
Dreamland
>>> print metadata['Exif.Photo.DateTimeOriginal']
2007-09-28 03:00:00
>>> print metadata['Iptc.Application2.Keywords']
('test', 'photo')
>>> print metadata['Exif.Photo.PixelXDimension']
1
>>> print metadata['Exif.Photo.PixelYDimension']
1

>>> photo.description = "Image for testing"
>>> photo.save()
>>> photo.sync_metadata_to_file()
True
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageDescription']
Image for testing

>>> photo.metadata_sync_enabled = False
>>> photo.description = "Sample image for testing purposes"
>>> photo.save()
>>> print photo.sync_metadata_to_file()
False

>>> # Sometimes the image isn't a JPEG.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.tif')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'TIFF')
>>> photo = Photo()
>>> photo.owner = user
>>> photo.description = 'Test file'
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = False
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> print photo.sync_metadata_to_file()
True
>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> print metadata['Exif.Image.ImageWidth']
1
>>> print metadata['Exif.Image.ImageLength']
1

>>> # Sometimes metadata can't be read from the image.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.pcx')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'PCX')
>>> photo = Photo()
>>> photo.owner = user
>>> photo.description = 'Test file'
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> print photo.metadata_sync_enabled
True
>>> print photo.sync_metadata_to_file()
False
>>> print photo.metadata_sync_enabled
False

>>> # Sometimes metadata can't be written to the image.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.bmp')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'BMP')
>>> photo = Photo()
>>> photo.owner = user
>>> photo.description = 'Test file'
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> print photo.metadata_sync_enabled
True
>>> print photo.sync_metadata_to_file()
False
>>> print photo.metadata_sync_enabled
False


>>> # Test Photo.sync_metadata_from_file()

>>> # Set things up.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
>>> User.objects.all().delete()

>>> metadata = pyexiv2.Image(file_path)
>>> metadata.readMetadata()
>>> metadata['Exif.Image.ImageDescription'] = "Test file"
>>> metadata['Exif.Image.Artist'] = "Adam"
>>> metadata['Iptc.Application2.CountryName'] = "USA"
>>> metadata['Iptc.Application2.ProvinceState'] = "Virginia"
>>> metadata['Iptc.Application2.City'] = "Blacksburg"
>>> metadata['Iptc.Application2.SubLocation'] = "Dreamland"
>>> try:
...     metadata['Exif.Photo.DateTimeOriginal'] = datetime.datetime(
...         2007, 9, 28, 3, 0)
... except TypeError:
...     pass
>>> metadata['Iptc.Application2.Keywords'] = ['test', 'photo']
>>> metadata.writeMetadata()

>>> user = User.objects.create(username="Adam")
>>> album = Album.objects.create(owner=user, name="Test")
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.is_jpeg = True
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> photo.sync_metadata_from_file()
True

>>> print photo.description
Test file
>>> print photo.artist
Adam
>>> print photo.country
USA
>>> print photo.province_state
Virginia
>>> print photo.city
Blacksburg
>>> print photo.location
Dreamland
>>> print photo.time_created
2007-09-28 03:00:00
>>> print photo.get_keywords()
[u'test', u'photo']

>>> photo.sync_metadata_from_file()
False
>>> # Nothing should have changed.
>>> print photo.description
Test file
>>> print photo.artist
Adam
>>> print photo.country
USA
>>> print photo.province_state
Virginia
>>> print photo.city
Blacksburg
>>> print photo.location
Dreamland
>>> print photo.time_created
2007-09-28 03:00:00
>>> print photo.get_keywords()
[u'test', u'photo']

>>> metadata = pyexiv2.Image(photo.image.path)
>>> metadata.readMetadata()
>>> metadata['Exif.Image.ImageDescription'] = "Image for testing"
>>> metadata.writeMetadata()
>>> photo.sync_metadata_from_file()
True
>>> print photo.description
Image for testing

>>> photo.metadata_sync_enabled = False
>>> photo.description = "Image for testing"
>>> photo.save()
>>> print photo.sync_metadata_from_file()
False

>>> # Sometimes metadata can't be read from the image.
>>> file_descriptor, file_path = tempfile.mkstemp(suffix='.pcx')
>>> os.close(file_descriptor)
>>> Image.new('RGB', (1,1)).save(file_path, 'PCX')
>>> photo = Photo()
>>> photo.owner = user
>>> image = open(file_path)
>>> photo.image = ImageFile(image)
>>> photo.album = album
>>> photo.save()
>>> image.close()
>>> os.remove(file_path)
>>> print photo.metadata_sync_enabled
True
>>> print photo.sync_metadata_from_file()
False
>>> print photo.metadata_sync_enabled
False

"""
