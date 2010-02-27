from django.conf.urls.defaults import patterns, url

from photasm.photos.models import Photo

info_dict = {
    'queryset': Photo.objects.all(),
}

urlpatterns = patterns(
    'photasm.photos.views',

    url(r'^$', 'home', name='home'),

    url(r'^(?P<object_id>\d+)/$', 'photo_detail',
        dict(info_dict, template_name="photos/photo_detail.html"),
        "photo_detail"),

    url(r'^upload/$', 'photo_upload'),

    url(r'^(?P<object_id>\d+)/edit/$', 'photo_edit'),
)

urlpatterns += patterns(
    'django.views.generic',
)
