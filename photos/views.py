from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import list_detail

from photosharing.photos.models import Photo, PhotoEditForm, PhotoUploadForm


def photo_list(request, queryset, *args, **kwargs):
    return list_detail.object_list(request, queryset, *args, **kwargs)


def photo_detail(request, queryset, *args, **kwargs):
    return list_detail.object_detail(request, queryset, *args, **kwargs)


@login_required
def photo_upload(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            request.user.message_set.create(
                message="Your photograph was added successfully.")
            return HttpResponseRedirect(reverse("photo_detail",
                                                args=[form.instance.id]))
    else:
        form = PhotoUploadForm()

    return render_to_response('photos/photo_upload.html', {
        'form': form,
    })


@login_required
def photo_edit(request, object_id):
    if request.method == 'POST':
        object = get_object_or_404(Photo, pk=object_id)
        form = PhotoEditForm(request.POST, instance=object)

        if form.is_valid():
            form.save()
            request.user.message_set.create(
                message="Your photograph was successfully updated.")
            return HttpResponseRedirect(reverse("photo_detail",
                                                args=[object_id]))

    else:
        object = get_object_or_404(Photo, pk=object_id)
        form = PhotoEditForm(instance=object)

    return render_to_response('photos/photo_edit.html', {
        'form': form,
    })
