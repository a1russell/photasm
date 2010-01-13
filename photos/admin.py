from django.contrib import admin

from photasm.photos.models import Album, Photo, PhotoTag


class PhotoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        photo_data = form.cleaned_data['data']
        if photo_data is not None and photo_data.content_type == "image/jpeg":
            obj.is_jpeg = True
        
        obj.save()
        form.save_m2m()
        
        # object is being added
        if change is False:
            # Remember user-entered fields.
            description = obj.description
            artist = obj.artist
            country = obj.country
            province_state = obj.province_state
            city = obj.city
            location = obj.location
            time_created = obj.time_created
            keywords = obj.keywords.all()

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
