from django.conf import settings
from django.conf.urls.defaults import (
    include,
    handler404,
    handler500,
    patterns,
)

from django.contrib import admin
admin.autodiscover()

handler404, handler500  # Keep PyFlakes happy.

urlpatterns = patterns(
    '',

    (r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    (r'^', include('photasm.photos.urls')),
)

if settings.DEBUG:
    # Serve static media
    urlpatterns += patterns(
        '',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_DOC_ROOT}),
    )

    # Serve uploaded media
    # The URL regex for this pattern should be related to settings.MEDIA_URL.
    urlpatterns += patterns(
        '',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
