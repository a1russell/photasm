import math
import os
from StringIO import StringIO
import tempfile

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.db import models
from django.forms import ModelForm
from PIL import Image
import pyexiv2

from photasm.photos.image_metadata import *


class Album(models.Model):
    """\
    A photograph album.
    
    This is a collection of Photo objects.  It is intended to be a way for
    the user to organize his photographs in a fashion reflecting real life.
    
    """
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class PhotoTag(models.Model):
    """\
    A keyword or tag related to a photograph, provided by the user.
    
    Different photographs that are related in subject matter should share a
    common PhotoTag.
    
    """
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Photo(models.Model):
    """\
    A photograph.
    
    Each Photo object belongs to one owner and one album. Certain image
    metadata fields are synchronized between the database and the filesystem.
    
    """
    owner = models.ForeignKey(User)

    data = models.ImageField(upload_to="photos/%Y/%m/%d",
                             height_field="image_height",
                             width_field="image_width")

    thumbnail = models.ImageField(upload_to="thumbs/%Y/%m/%d",
                                  editable=False, null=True)

    description = models.CharField(blank=True, max_length=2000)
    """\
    The title of the image.
    
    This may be a comment such as "1988 company picnic" or the like.
    
    Corresponding image metadata keys:
        Exif.Image.ImageDescription
        Iptc.Application2.Caption
    
    """

    artist = models.CharField(blank=True, max_length=32)
    """\
    Records the name of the camera owner, photographer or image creator.
    
    The detailed format is not specified, but it is recommended that the
    information be written as in the example below for ease of
    interoperability. When the field is left blank, it is treated as unknown.
    
    Ex.:
        "Camera owner, John Smith; Photographer, Michael Brown;
        Image creator, Ken James"
    
    Corresponding image metadata keys:
        Exif.Image.Artist
        Iptc.Application2.Byline
    
    """

    country = models.CharField("country name", blank=True, max_length=64)
    """\
    Full name of the country the content is focusing on.
    
    A list of country names can be obtained at the following URL:
        http://www.iso.org/iso/english_country_names_and_code_elements
    
    Corresponding image metadata keys:
        Iptc.Application2.CountryName
    
    """

    province_state = models.CharField("province/state", blank=True,
                                      max_length=32)
    """\
    Name of the state or province of object data origin.
    
    Corresponding image metadata keys:
        Iptc.Application2.ProvinceState
    
    """

    city = models.CharField(blank=True, max_length=32)
    """\
    Name of the city of object data origin.
    
    Corresponding image metadata keys:
        Iptc.Application2.City
    
    """

    location = models.CharField(blank=True, max_length=32,
                                help_text="location within a city")
    """\
    The location within a city from which the object data originates.
    
    Corresponding image metadata keys:
        Iptc.Application2.SubLocation
    
    """

    time_created = models.DateTimeField(null=True, blank=True,
                                        help_text="date photo was taken")
    """\
    Date the photo was taken.
    
    Technically, the date the original image data was generated. Designates
    the date the intellectual content of the object data was created rather
    than the date of the creation of the physical representation.
    
    Corresponding image metadata keys:
        Exif.Photo.DateTimeOriginal
        Iptc.Application2.DateCreated
        Iptc.Application2.TimeCreated
    
    """

    keywords = models.ManyToManyField(PhotoTag, null=True, blank=True)
    """\
    Specific information retrieval words.
    
    It is expected that a provider of various types of data that are related
    in subject matter uses the same keyword.
    
    Corresponding image metadata keys:
        Iptc.Application2.Keywords
    
    """

    image_width = models.IntegerField(editable=False)
    """\
    Image width.
    
    Corresponding image metadata keys:
        Exif.Image.ImageWidth (if not JPEG)
        Exif.Photo.PixelXDimension (if JPEG)
    
    """

    image_height = models.IntegerField(editable=False)
    """\
    Image height.
    
    Corresponding image metadata keys:
        Exif.Image.ImageLength (if not JPEG)
        Exif.Photo.PixelYDimension (if JPEG)
    
    """
    
    is_jpeg = models.BooleanField(default=False, editable=False)
    
    metadata_sync_enabled = models.BooleanField(default=True)

    album = models.ForeignKey(Album)

    def __unicode__(self):
        repr = "%s's pic #%d" % (self.owner.username, self.id)
        if len(self.description) > 0:
            repr += ": " + self.description
        return repr
    
    def save(self, *args, **kwargs):
        try:
            # Check if the data property has changed.
            # If so, delete the old image on the filesystem.
            old_obj = Photo.objects.get(pk=self.pk)
            if old_obj.data.path != self.data.path:
                path = old_obj.data.path
                default_storage.delete(path)
                if old_ob.thumbnail:
                    path = old_obj.thumbnail.path
                    default_storage.delete(path)
        except:
            pass
        super(Photo, self).save(*args, **kwargs)
    
    @models.permalink
    def get_absolute_url(self):
        return ('photo_detail', (), {'object_id': self.id})
    
    def get_keywords(self):
        """\
        Returns the photograph keywords as a list of strings.

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
        >>> photo.data = ImageFile(image)
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
        
        """
        keywords = []
        for keyword in self.keywords.all():
            keywords.append(keyword.name)
        return keywords
    
    def set_keywords(self, keywords):
        """\
        Sets the keywords from a list of strings.
        
        Parameters:
        keywords -- the list of keywords to set

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
        >>> photo.data = ImageFile(image)
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
        
        """
        self.keywords.clear()

        if not keywords:
            return
        
        for keyword in keywords:
            try:
                photo_tag = PhotoTag.objects.get(name__iexact=keyword)
            except ObjectDoesNotExist:
                self.keywords.create(name=keyword)
                continue
            except PhotoTag.MultipleObjectsReturned:
                continue
            self.keywords.add(photo_tag)
    
    def create_thumbnail(self):
        """\
        Creates a thumbnail version of the image.

        The embedded thumnail in a JPEG will be used if it exists.
        If the image is JPEG and it does not already have a thumbnail, it
        will be embedded.

        Note that calling this method will also call Photo.save().

        >>> import datetime

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
        >>> photo.data = ImageFile(image)
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
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> photo.data = ImageFile(image)
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
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> photo.data = ImageFile(image)
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
        >>> photo.data = ImageFile(image)
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
        >>> metadata = pyexiv2.Image(photo.data.path)
        >>> metadata.readMetadata()
        >>> embedded = metadata.getThumbnailData()[1]
        >>> external = open(photo.thumbnail.path).read()
        >>> print embedded == external
        True

        """
        needs_thumbnail_embed = False
        if self.is_jpeg:
            metadata = pyexiv2.Image(self.data.path)
            metadata.readMetadata()
            try:
                thumb_data = metadata.getThumbnailData()
            except IOError:
                needs_thumbnail_embed = True
            else:
                thumb = StringIO(thumb_data[1])
                thumb_image = Image.open(thumb)
                thumb_fd, thumb_path = tempfile.mkstemp()
                os.close(thumb_fd)
                thumb_image.save(thumb_path, thumb_image.format)
                thumb.close()
                thumb = open(thumb_path)
                self.thumbnail = ImageFile(thumb)
                self.save()
                thumb.close()
                os.remove(thumb_path)
                return

        THUMB_SZ = 19200
        thumb_sz_coefficient = math.sqrt(THUMB_SZ) / \
                               math.sqrt(self.image_height * self.image_width)
        thumb_width = int(round(self.image_width * thumb_sz_coefficient))
        thumb_height = int(round(self.image_height * thumb_sz_coefficient))
        
        thumb_image = Image.open(self.data.path)
        if (self.image_width * self.image_height) > THUMB_SZ:
            thumb_image.thumbnail((thumb_width, thumb_height))
        thumb_fd, thumb_path = tempfile.mkstemp()
        os.close(thumb_fd)
        thumb_image.save(thumb_path, thumb_image.format)
        thumb = open(thumb_path)
        self.thumbnail = ImageFile(thumb)
        self.save()
        thumb.close()

        if needs_thumbnail_embed:
            metadata.setThumbnailFromJpegFile(thumb_path)
            metadata.writeMetadata()

        os.remove(thumb_path)
    
    def sync_metadata_to_file(self):
        """\
        Synchronizes the image metadata from the object to the filesystem.
        
        This stores certain properties of the object to the image file
        itself as Exif and/or IPTC tags, allowing the information to be
        portable outside of this application. Metadata is only actually
        written to the filesystem if the values do not match up, however.
        
        Returns True if metadata needed to be written to the file;
        False otherwise.

        >>> # Set things up.
        >>> import datetime
        >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
        >>> os.close(file_descriptor)
        >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
        >>> User.objects.all().delete()
       
        >>> user = User.objects.create(username="Adam")
        >>> album = Album.objects.create(owner=user, name="Test")
        >>> photo = Photo()
        >>> photo.owner = user
        >>> image = open(file_path)
        >>> photo.data = ImageFile(image)
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
       
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> photo.data = ImageFile(image)
        >>> photo.album = album
        >>> photo.is_jpeg = False
        >>> photo.save()
        >>> image.close()
        >>> os.remove(file_path)
        >>> print photo.sync_metadata_to_file()
        True
        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> photo.data = ImageFile(image)
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
        >>> photo.data = ImageFile(image)
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
        
        """
        if not self.metadata_sync_enabled:
            return False
        
        try:
            image_metadata = pyexiv2.Image(self.data.path)
            image_metadata.readMetadata()
        except IOError:
            self.metadata_sync_enabled = False
            self.save()
            return False
        
        mod = False # whether or not file actually needs written to
        
        # sync description
        mod = sync_value_to_exif_and_iptc(self.description, image_metadata,
                                          'Exif.Image.ImageDescription',
                                          'Iptc.Application2.Caption') or mod
        
        # sync artist
        mod = sync_value_to_exif_and_iptc(self.artist, image_metadata,
                                          'Exif.Image.Artist',
                                          'Iptc.Application2.Byline') or mod
        
        # sync country
        mod = sync_value_to_iptc(self.country, image_metadata,
                                 'Iptc.Application2.CountryName') or mod
        
        # sync province_state
        mod = sync_value_to_iptc(self.province_state, image_metadata,
                                 'Iptc.Application2.ProvinceState') or mod
        
        # sync city
        mod = sync_value_to_iptc(self.city, image_metadata,
                                 'Iptc.Application2.City') or mod
        
        # sync location
        mod = sync_value_to_iptc(self.location, image_metadata,
                                 'Iptc.Application2.SubLocation') or mod
        
        # sync time_created
        mod = sync_datetime_to_exif_and_iptc(self.time_created,
            image_metadata, 'Exif.Photo.DateTimeOriginal',
            'Iptc.Application2.DateCreated', 'Iptc.Application2.TimeCreated')\
            or mod
        
        # sync keywords
        mod = sync_value_to_iptc(self.get_keywords(), image_metadata,
                                 'Iptc.Application2.Keywords') or mod
        
        # sync image_width
        mod = sync_value_to_exif(self.image_width, image_metadata,
                                 get_image_width_key(self.is_jpeg)) or mod
        
        # sync image_height
        mod = sync_value_to_exif(self.image_height, image_metadata,
                                 get_image_height_key(self.is_jpeg)) or mod
        
        if mod:
            try:
                image_metadata.writeMetadata()
            except IOError:
                self.metadata_sync_enabled = False
                self.save()
                return False
        
        return mod
    
    def sync_metadata_from_file(self, commit=True):
        """\
        Synchronizes the image metadata from the filesystem to the object.
        
        This reads certain properties of the object from Exif and/or IPTC tags 
        in the image file itself, allowing the information to be portable
        from outside of this application. Metadata is only actually
        written to the database if the values do not match up, however.
        
        Returns True if metadata needed to be written to the database;
        False otherwise.

        >>> # Set things up.
        >>> import datetime
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
        >>> photo.data = ImageFile(image)
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

        >>> metadata = pyexiv2.Image(photo.data.path)
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
        >>> photo.data = ImageFile(image)
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
        if not self.metadata_sync_enabled:
            return False

        try:
            image_metadata = pyexiv2.Image(self.data.path)
            image_metadata.readMetadata()
        except IOError:
            self.metadata_sync_enabled = False
            self.save()
            return False
        
        mod_instance = False  # whether or not database needs written to
        
        # sync description
        mod_attr = not value_synced_with_exif_and_iptc(
            self.description, image_metadata,
            'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
        mod_instance = mod_attr or mod_instance
        if mod_attr:
            value = read_value_from_exif_and_iptc(image_metadata,
                'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
            if value is None:
                value = str()
            self.description = value
        
        # sync artist
        mod_attr = not value_synced_with_exif_and_iptc(
            self.artist, image_metadata,
            'Exif.Image.Artist', 'Iptc.Application2.Byline')
        mod_instance = mod_attr or mod_instance
        if mod_attr:
            value = read_value_from_exif_and_iptc(image_metadata,
                'Exif.Image.Artist', 'Iptc.Application2.Byline')
            if value is None:
                value = str()
            self.artist = value
        
        # sync country
        mod_attr = not value_synced_with_iptc(self.country, image_metadata,
                                              'Iptc.Application2.CountryName')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.CountryName' in image_metadata.iptcKeys() and
            mod_attr):
            value = image_metadata['Iptc.Application2.CountryName']
            if value is None:
                value = str()
            self.country = value
        
        # sync province_state
        mod_attr = not value_synced_with_iptc(
            self.province_state, image_metadata,
            'Iptc.Application2.ProvinceState')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.ProvinceState' in image_metadata.iptcKeys() and
            mod_attr):
            value = image_metadata['Iptc.Application2.ProvinceState']
            if value is None:
                value = str()
            self.province_state = value
        
        # sync city
        mod_attr = not value_synced_with_iptc(self.city, image_metadata,
                                              'Iptc.Application2.City')
        mod_instance = mod_attr or mod_instance
        if 'Iptc.Application2.City' in image_metadata.iptcKeys() and mod_attr:
            value = image_metadata['Iptc.Application2.City']
            if value is None:
                value = str()
            self.city = value
        
        # sync location
        mod_attr = not value_synced_with_iptc(self.location, image_metadata,
                                              'Iptc.Application2.SubLocation')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.SubLocation' in image_metadata.iptcKeys() and
            mod_attr):
            value = image_metadata['Iptc.Application2.SubLocation']
            if value is None:
                value = str()
            self.location = value
        
        # sync time_created
        mod_attr = not datetime_synced_with_exif_and_iptc(
            self.time_created, image_metadata,
            'Exif.Photo.DateTimeOriginal', 'Iptc.Application2.DateCreated',
            'Iptc.Application2.TimeCreated')
        mod_instance = mod_attr or mod_instance
        if mod_attr:
            self.time_created = read_datetime_from_exif_and_iptc(
                image_metadata, 'Exif.Photo.DateTimeOriginal',
                'Iptc.Application2.DateCreated',
                'Iptc.Application2.TimeCreated')
        
        # sync keywords
        mod_attr = not value_synced_with_iptc(self.get_keywords(),
            image_metadata, 'Iptc.Application2.Keywords')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.Keywords' in image_metadata.iptcKeys() and
            mod_attr):
            self.set_keywords(image_metadata['Iptc.Application2.Keywords'])
        
        if mod_instance and commit:
            self.save()
        
        return mod_instance


class PhotoUploadForm(ModelForm):
    """\
    Form presented to the user for uploading a Photo.
    
    This form does not include any of the image metadata properties since
    they should be read from the file itself upon upload. This eliminates
    the possibility of a user overwriting metadata stored in the file.
    
    """
    class Meta:
        model = Photo
        fields = ('album', 'data',)


class PhotoEditForm(ModelForm):
    """\
    Form presented to the user for editing a Photo.
    
    This form does not allow the user to change the actual image file
    associated with the Photo object, as the two are tightly coupled.
    Since image metadata should have already been read from the file upon
    upload, changes to the values in this form should be synchronized back
    to the image on the filesystem.
    
    """
    class Meta:
        model = Photo
        exclude = ('owner', 'data', 'metadata_sync_enabled',)
