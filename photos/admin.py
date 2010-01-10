from django.contrib import admin

from photasm.photos.models import Album, Photo, PhotoTag


class PhotoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        
        # object is being added
        if change is False:
            # Remember user-entered fields.
            description = obj.description
            artist = obj.artist
            country = obj.country
            province_state = obj.province_state
            city = obj.city
            location = obj.location
            date_created = obj.date_created
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
            if date_created:
                obj.date_created = date_created
                sync_back = True
            if keywords:
                obj.keywords = keywords
                sync_back = True

            if sync_back is True:
                obj.save()
                obj.sync_metadata_to_file()

        # object is being changed
        else:
            obj.sync_metadata_to_file()


admin.site.register(Photo, PhotoAdmin)
admin.site.register((Album, PhotoTag))
