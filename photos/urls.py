from django.conf.urls.defaults import patterns, url

from photasm.photos.models import Photo, Album

photo_info = {
    'queryset': Photo.objects.all(),
}

album_info = {
    'queryset': Album.objects.all(),
}

urlpatterns = patterns(
    'photasm.photos.views',

    url(r'^$', 'home', name='home'),

    url(r'^(?P<object_id>\d+)/$', 'photo_detail',
        dict(photo_info, template_name="photos/photo_detail.html"),
        "photo_detail"),

    url(r'^upload/$', 'photo_upload'),

    url(r'^(?P<object_id>\d+)/edit/$', 'photo_edit'),
)

urlpatterns += patterns(
    'django.views.generic',

    url(r'^albums/(?P<object_id>\d+)/$', 'list_detail.object_detail',
        dict(album_info, template_name="photos/album_detail.html"),
        "album_detail"),
)
