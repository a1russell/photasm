from photosharing.photos.models import Album, PhotoTag, Photo
from django.contrib import admin


admin.site.register((Photo, PhotoTag, Album))
