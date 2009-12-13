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
        # TODO: Write updated Exif & IPTC back to the image.
        pass
    
    def sync_metadata_from_file(self):
        # TODO: Retrieve properties from Exif & IPTC.
        pass
    
    def definition_metadata_is_in_sync(self):
        return value_synced_with_exif_and_iptc(
            self.description, self.data.path,
            'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    
    def artist_metadata_is_in_sync(self):
        return value_synced_with_exif_and_iptc(self.artist, self.data.path,
            'Exif.Image.Artist', 'Iptc.Application2.Byline')
    
    def country_metadata_is_in_sync(self):
        return value_synced_with_iptc(self.country, self.data.path,
            'Iptc.Application2.CountryName')
    
    def province_state_metadata_is_in_sync(self):
        return value_synced_with_iptc(self.province_state, self.data.path,
            'Iptc.Application2.ProvinceState')
    
    def city_metadata_is_in_sync(self):
        return value_synced_with_iptc(self.city, self.data.path,
            'Iptc.Application2.City')
    
    def location_metadata_is_in_sync(self):
        return value_synced_with_iptc(self.location, self.data.path,
            'Iptc.Application2.SubLocation')
    
    def date_created_metadata_is_in_sync(self):
        return value_synced_with_exif_and_iptc(
            self.date_created, self.data.path,
            'Exif.Image.DateTimeOriginal', 'Iptc.Application2.DateCreated')
    
    def keywords_metadata_is_in_sync(self):
        # TODO: Make sure only keyword order doesn't force sync.
        return value_synced_with_iptc(self.keywords, self.data.path,
            'Iptc.Application2.Keywords')
    
    def image_width_metadata_is_in_sync(self):
        return value_synced_with_exif(self.image_width, self.data.path,
            'Exif.Image.ImageWidth')
    
    def image_height_metadata_is_in_sync(self):
        return value_synced_with_exif(self.image_height, self.data.path,
            'Exif.Image.ImageHeight')


class PhotoUploadForm(ModelForm):
    class Meta:
        model = Photo
        fields = ('owner', 'album', 'data',)


class PhotoEditForm(ModelForm):
    class Meta:
        model = Photo
        exclude = ('data',)
