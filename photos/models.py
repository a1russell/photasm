from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.db import models
from django.forms import ModelForm

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

    album = models.ForeignKey(Album)

    def __unicode__(self):
        repr = "%s's pic #%d" % (self.owner.username, self.id)
        if len(self.description) > 0:
            repr += ": " + self.description
        return repr
    
    def save(self, *args, **kwargs):
        try:
            old_obj = Photo.objects.get(pk=self.pk)
            if old_obj.image.path != self.image.path:
                path = old_obj.image.path
                default_storage.delete(path)
        except:
            pass
        super(Photo, self).save(*args, **kwargs)
    
    @models.permalink
    def get_absolute_url(self):
        return ('photo_detail', (), {'object_id': self.id})
    
    def get_keywords(self):
        keywords = []
        for keyword in self.keywords.all():
            keywords.append(keyword.name)
        return keywords
    
    def set_keywords(self, keywords):
        if not keywords:
            return
        
        self.keywords.clear()
        for keyword in keywords:
            try:
                photo_tag = PhotoTag.objects.get(name__iexact=keyword)
            except ObjectDoesNotExist:
                self.keywords.create(name=keyword)
                continue
            except PhotoTag.MultipleObjectsReturned:
                continue
            self.keywords.add(photo_tag)
    
    def sync_metadata_to_file(self):
        image_metadata = pyexiv2.Image(self.data.path)
        image_metadata.readMetadata()
        
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
            image_metadata.writeMetadata()
        
        return mod
    
    def sync_metadata_from_file(self, commit=True):
        image_metadata = pyexiv2.Image(self.data.path)
        image_metadata.readMetadata()
        
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
        mod_attr = not value_synced_with_iptc(self.keywords.all(),
            image_metadata, 'Iptc.Application2.Keywords')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.Keywords' in image_metadata.iptcKeys() and
            mod_attr):
            self.set_keywords(image_metadata['Iptc.Application2.Keywords'])
        
        # sync image_width
        image_width_key = get_image_width_key(self.is_jpeg)
        mod_attr = not value_synced_with_exif(self.image_width, image_metadata,
                                              image_width_key)
        mod_instance = mod_attr or mod_instance
        if image_width_key in image_metadata.exifKeys() and mod_attr:
            self.image_width = image_metadata[image_width_key]
        
        # sync image_height
        image_height_key = get_image_height_key(self.is_jpeg)
        mod_attr = not value_synced_with_exif(
            self.image_height, image_metadata, image_height_key)
        mod_instance = mod_attr or mod_instance
        if image_height_key in image_metadata.exifKeys() and mod_attr:
            self.image_height = image_metadata[image_height_key]
        
        if mod_instance and commit:
            self.save()
        
        return mod_instance


class PhotoUploadForm(ModelForm):
    class Meta:
        model = Photo
        fields = ('album', 'data',)


class PhotoEditForm(ModelForm):
    class Meta:
        model = Photo
        exclude = ('owner', 'data',)
