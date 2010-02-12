from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic import list_detail

from photasm.photos.models import Photo, PhotoEditForm, PhotoUploadForm


def photo_list(request, queryset, *args, **kwargs):
    return list_detail.object_list(request, queryset, *args, **kwargs)


def photo_detail(request, queryset, *args, **kwargs):
    return list_detail.object_detail(request, queryset, *args, **kwargs)


@login_required
def photo_upload(request):
    """\
    Uploads a Photo.
    
    This reads the image metadata from the file on the filesystem into the
    corresponding properties in the Photo object.
    
    It is assumed that no Photo properties associated with the image metadata
    are submitted, as this would overwrite the metadata in the file without
    informing the user of previous values.
    
    """
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)

        if form.is_valid():
            photo = form.cleaned_data['image']
            photo_content_type = None
            
            new_photo = form.save(commit=False)
            new_photo.owner = request.user
            
            try:
                photo_content_type = photo.content_type
            except AttributeError:
                pass
            if photo_content_type == "image/jpeg":
                new_photo.is_jpeg = True
            
            new_photo.save()
            form.save_m2m()
            new_photo.create_thumbnail()
            new_photo.sync_metadata_from_file()
            
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
    """\
    Edits a Photo.
    
    This writes the image metadata from the appropriate properties back to
    the file on the filesystem.
    
    It is assumed that the image data associated with the Photo is not
    submitted to this view, as this would most likely write metadata to the
    newly submitted image that was associated to the old one.
    
    """
    if request.method == 'POST':
        object = get_object_or_404(Photo, pk=object_id)
        form = PhotoEditForm(request.POST, instance=object)

        if form.is_valid():
            form.save()
            object.sync_metadata_to_file()
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
