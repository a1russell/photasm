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

    # Exif ImageLength
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
        
        # sync date_created
        mod = sync_value_to_exif_and_iptc(self.date_created, image_metadata,
                                          'Exif.Image.DateTimeOriginal',
                                          'Iptc.Application2.DateCreated') \
                                          or mod
        
        # sync keywords
        mod = sync_value_to_iptc(self.keywords.all(), image_metadata,
                                 'Iptc.Application2.Keywords') or mod
        
        # sync image_width
        mod = sync_value_to_exif(self.image_width, image_metadata,
                                 'Exif.Image.ImageWidth') or mod
        
        # sync image_height
        mod = sync_value_to_exif(self.image_height, image_metadata,
                                 'Exif.Image.ImageLength') or mod
        
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
            self.description = read_value_from_exif_and_iptc(image_metadata,
                'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
        
        # sync artist
        mod_attr = not value_synced_with_exif_and_iptc(
            self.artist, image_metadata,
            'Exif.Image.Artist', 'Iptc.Application2.Byline')
        mod_instance = mod_attr or mod_instance
        if mod_attr:
            self.artist = read_value_from_exif_and_iptc(image_metadata,
                'Exif.Image.Artist', 'Iptc.Application2.Byline')
        
        # sync country
        mod_attr = not value_synced_with_iptc(self.country, image_metadata,
                                              'Iptc.Application2.CountryName')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.CountryName' in image_metadata.iptcKeys() and
            mod_attr):
            self.country = image_metadata['Iptc.Application2.CountryName']
        
        # sync province_state
        mod_attr = not value_synced_with_iptc(
            self.province_state, image_metadata,
            'Iptc.Application2.ProvinceState')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.ProvinceState' in image_metadata.iptcKeys() and
            mod_attr):
            self.province_state = \
                image_metadata['Iptc.Application2.ProvinceState']
        
        # sync city
        mod_attr = not value_synced_with_iptc(self.city, image_metadata,
                                              'Iptc.Application2.City')
        mod_instance = mod_attr or mod_instance
        if 'Iptc.Application2.City' in image_metadata.iptcKeys() and mod_attr:
            self.city = image_metadata['Iptc.Application2.City']
        
        # sync location
        mod_attr = not value_synced_with_iptc(self.location, image_metadata,
                                              'Iptc.Application2.SubLocation')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.SubLocation' in image_metadata.iptcKeys() and
            mod_attr):
            self.location = image_metadata['Iptc.Application2.SubLocation']
        
        # sync date_created
        mod_attr = not value_synced_with_exif_and_iptc(
            self.date_created, image_metadata,
            'Exif.Image.DateTimeOriginal', 'Iptc.Application2.DateCreated')
        mod_instance = mod_attr or mod_instance
        if mod_attr:
            self.date_created = read_value_from_exif_and_iptc(image_metadata,
                'Exif.Image.DateTimeOriginal', 'Iptc.Application2.DateCreated')
        
        # sync keywords
        mod_attr = not value_synced_with_iptc(self.keywords.all(),
            image_metadata, 'Iptc.Application2.Keywords')
        mod_instance = mod_attr or mod_instance
        if ('Iptc.Application2.Keywords' in image_metadata.iptcKeys() and
            mod_attr):
            for keyword in image_metadata['Iptc.Application2.Keywords']:
                continue
                # TODO: Implement this. Handle PhotoTag objects.
                self.keywords.add(keyword)
        
        # sync image_width
        mod_attr = not value_synced_with_exif(self.image_width, image_metadata,
                                              'Exif.Image.ImageWidth')
        mod_instance = mod_attr or mod_instance
        if 'Exif.Image.ImageWidth' in image_metadata.exifKeys() and mod_attr:
            self.image_width = image_metadata['Exif.Image.ImageWidth']
        
        # sync image_height
        mod_attr = not value_synced_with_exif(
            self.image_height, image_metadata, 'Exif.Image.ImageLength')
        mod_instance = mod_attr or mod_instance
        if 'Exif.Image.ImageLength' in image_metadata.exifKeys() and mod_attr:
            self.image_height = image_metadata['Exif.Image.ImageLength']
        
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
