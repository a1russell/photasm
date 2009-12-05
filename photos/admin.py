from django.contrib import admin

from photosharing.photos.models import Album, Photo, PhotoTag


class PhotoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # http://code.djangoproject.com/browser/django/trunk/django/contrib/admin/options.py:
        # ``change`` is True if the object is being changed, and False if it's being added.
        obj.save()


admin.site.register(Photo, PhotoAdmin)
admin.site.register((Album, PhotoTag))
