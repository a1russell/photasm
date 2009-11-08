from django.db import models
from django.contrib.auth.models import User


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

    # Exif ImageDescription, IPTC Caption 
    _description = models.CharField(max_length=2000)

    # Exif Artist, IPTC Byline
    _artist = models.CharField(max_length=32)

    # IPTC CountryName
    _country = models.CharField(max_length=64)

    # IPTC ProvinceState
    _state = models.CharField(max_length=32)

    # IPTC City
    _city = models.CharField(max_length=32)

    # IPTC SubLocation
    _location = models.CharField(max_length=32)

    # Exif DateTimeOriginal, IPTC DateCreated
    _date_created = models.DateField()

    # IPTC Keywords
    _keywords = models.ManyToManyField(PhotoTag)

    # Exif ImageWidth
    _image_width = models.IntegerField()

    # Exif ImageHeight
    _image_height = models.IntegerField()

    album = models.ForeignKey(Album)

    def __unicode__(self):
        return self.description

