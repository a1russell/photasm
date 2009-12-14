from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm

from photosharing.photos.image_metadata import *


class Album(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class PhotoTag(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Photo(models.Model):
    owner = models.ForeignKey(User)

    data = models.ImageField(upload_to="photos/%Y/%m/%d",
                             height_field="image_height",
                             width_field="image_width")

    # Exif ImageDescription, IPTC Caption 
    description = models.CharField(blank=True, max_length=2000)

    # Exif Artist, IPTC Byline
    artist = models.CharField(blank=True, max_length=32)

    # IPTC CountryName
    country = models.CharField("country name", blank=True, max_length=64)

    # IPTC ProvinceState
    province_state = models.CharField("province/state", blank=True,
                                      max_length=32)

    # IPTC City
    city = models.CharField(blank=True, max_length=32)

    # IPTC SubLocation
    location = models.CharField(blank=True, max_length=32,
                                help_text="location within a city")

    # Exif DateTimeOriginal, IPTC DateCreated
    # date photo was taken
    date_created = models.DateField(null=True, blank=True,
                                    help_text="date original image data "\
                                              "was generated")

    # IPTC Keywords
    keywords = models.ManyToManyField(PhotoTag, null=True, blank=True)

    # Exif ImageWidth
    image_width = models.IntegerField(editable=False)

    # Exif ImageHeight
    image_height = models.IntegerField(editable=False)

    album = models.ForeignKey(Album)

    def __unicode__(self):
        repr = "%s's pic #%d" % (self.owner.username, self.id)
        if len(self.description) > 0:
            repr += ": " + self.description
        return repr
    
    def sync_metadata_to_file(self):
        image_metadata = pyexiv2.Image(self.data.path)
        image_metadata.readMetadata()
        
        mod = False # whether or not file actually needs written to
        
        mod = sync_value_to_exif_and_iptc(self.description, image_metadata,
                                          'Exif.Image.ImageDescription',
                                          'Iptc.Application2.Caption') or mod
        
        mod = sync_value_to_exif_and_iptc(self.artist, image_metadata,
                                          'Exif.Image.Artist',
                                          'Iptc.Application2.Byline') or mod
        
        mod = sync_value_to_iptc(self.country, image_metadata,
                                 'Iptc.Application2.CountryName') or mod
        
        mod = sync_value_to_iptc(self.province_state, image_metadata,
                                 'Iptc.Application2.ProvinceState') or mod
        
        mod = sync_value_to_iptc(self.city, image_metadata,
                                 'Iptc.Application2.City') or mod
        
        mod = sync_value_to_iptc(self.location, image_metadata,
                                 'Iptc.Application2.SubLocation') or mod
        
        mod = sync_value_to_exif_and_iptc(self.date_created, image_metadata,
                                          'Exif.Image.DateTimeOriginal',
                                          'Iptc.Application2.DateCreated') \
                                          or mod
        
        mod = sync_value_to_iptc(self.keywords, image_metadata,
                                 'Iptc.Application2.Keywords') or mod
        
        mod = sync_value_to_exif(self.image_width, image_metadata,
                                 'Exif.Image.ImageWidth') or mod
        
        mod = sync_value_to_exif(self.image_height, image_metadata,
                                 'Exif.Image.ImageHeight') or mod
        
        if mod:
            image_metadata.writeMetadata()
        
        return mod
    
    def sync_metadata_from_file(self):
        # TODO: Retrieve properties from Exif & IPTC.
        # TODO: Keep efficiency in mind.
        pass


class PhotoUploadForm(ModelForm):
    class Meta:
        model = Photo
        fields = ('owner', 'album', 'data',)


class PhotoEditForm(ModelForm):
    class Meta:
        model = Photo
        exclude = ('data',)
