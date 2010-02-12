from django.contrib import admin

from photasm.photos.models import Album, Photo, PhotoTag


class PhotoAdmin(admin.ModelAdmin):
    """\
    Django Admin form for adding and editing Photos.
    
    """
    def save_model(self, request, obj, form, change):
        """\
        Saves the Photo object.
        
        If the Photo is just being added, or if the image data associated to
        the Photo has been changed, image metadata is read from the file on the
        filesystem before applying the user-entered values for the properties
        and saving them back to the file on the filesystem. Otherwise, if the
        Photo is being changed without modifying its associated image data,
        the image metadata is simply written to the file on the filesystem.
        
        The change parameter is False if object is being added, and it is
        True if the object is being edited.
        
        """
        image_change = False
        try:
            old_obj = Photo.objects.get(pk=obj.pk)
            if old_obj.image.path != obj.image.path:
                image_change = True
        except:
            pass
        
        photo = form.cleaned_data['image']
        photo_content_type = None
        try:
            photo_content_type = photo.content_type
        except AttributeError:
            pass
        if photo_content_type == "image/jpeg":
            obj.is_jpeg = True
        
        obj.save()
        form.save_m2m()
        
        # object is being added or image field is being modified
        if change is False or image_change is True:
            # Remember user-entered fields.
            description = obj.description
            artist = obj.artist
            country = obj.country
            province_state = obj.province_state
            city = obj.city
            location = obj.location
            time_created = obj.time_created
            keywords = obj.keywords.all()

            obj.create_thumbnail()
            obj.sync_metadata_from_file()
            
            # Put user-entered fields back into object that may have
            # been overwritten by metadata sync.
            sync_back = False
            if description:
                obj.description = description
                sync_back = True
            if artist:
                obj.artist = artist
                sync_back = True
            if country:
                obj.country = country
                sync_back = True
            if province_state:
                obj.province_state = province_state
                sync_back = True
            if city:
                obj.city = city
                sync_back = True
            if location:
                obj.location = location
                sync_back = True
            if time_created:
                obj.time_created = time_created
                sync_back = True
            if keywords:
                obj.keywords = keywords
                form.save_m2m()
                sync_back = True

            if sync_back is True:
                obj.save()
                obj.sync_metadata_to_file()

        # object is being changed
        else:
            obj.sync_metadata_to_file()


admin.site.register(Photo, PhotoAdmin)
admin.site.register((Album, PhotoTag))
