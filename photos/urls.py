from django.conf.urls.defaults import *

from photosharing.photos.models import Photo

info_dict = {
    'queryset': Photo.objects.all(),
}

urlpatterns = patterns(
    'photosharing.photos.views',
    
    url(r'^$', 'photo_list',
        dict(info_dict, template_name="photos/photo_list.html"),
        "photo_list"),
    
    url(r'^(?P<object_id>\d+)/$', 'photo_detail',
        dict(info_dict, template_name="photos/photo_detail.html"),
        "photo_detail"),
    
    url(r'^upload/$', 'photo_upload'),
    
    url(r'^(?P<object_id>\d+)/edit/$', 'photo_edit'),
)

urlpatterns += patterns(
    'django.views.generic',
)
