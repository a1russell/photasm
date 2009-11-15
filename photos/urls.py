from django.conf.urls.defaults import *
from photosharing.photos.models import Photo

info_dict = {
    'queryset': Photo.objects.all(),
}

urlpatterns = patterns(
    'photosharing.photos.views',
)

urlpatterns += patterns(
    'django.views.generic',
    
    url(r'^$', 'list_detail.object_list',
        dict(info_dict, template_name="photos/photo_list.html"),
        "photo_list"),
    
    url(r'^(?P<object_id>\d+)/$', 'list_detail.object_detail',
        dict(info_dict, template_name="photos/photo_detail.html"),
        "photo_detail"),
)
