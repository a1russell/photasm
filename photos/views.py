from django.contrib.auth.decorators import login_required
from django.views.generic import list_detail

def photo_list(request, queryset, **kwargs):
    return list_detail.object_list(request, queryset, **kwargs)

def photo_detail(request, queryset, **kwargs):
    return list_detail.object_detail(request, queryset, **kwargs)
