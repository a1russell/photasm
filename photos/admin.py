from django.contrib import admin

from photosharing.photos.models import Album, Photo, PhotoTag


class PhotoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        if change is False: # object is being added
            obj.sync_metadata_from_file(commit=True)
        else: # object is being changed
            obj.save()
            obj.sync_metadata_to_file()
        


admin.site.register(Photo, PhotoAdmin)
admin.site.register((Album, PhotoTag))
