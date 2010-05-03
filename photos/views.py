from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from PIL import Image

from photasm.photos.models import (
    Album, Photo, PhotoEditForm, PhotoUploadForm, AlbumCreationForm)


@login_required
def home(request):
    album_list = Album.objects.filter(owner__id=request.user.id)
    return render_to_response('photos/home.html', {'album_list': album_list})


def photo_in_album(request, object_id):
    photo = get_object_or_404(Photo, pk=object_id)
    photos_in_album = Photo.objects.filter(album__id=photo.album.id)\
                           .order_by('id').values_list('id', flat=True)
    photo_count = len(photos_in_album)
    photo_index = list(photos_in_album).index(int(object_id)) + 1
    return render_to_response('photos/photo_in_album.html', {
        'object': photo,
        'photo_index': photo_index,
        'photo_count': photo_count,
    }, context_instance=RequestContext(request))


@login_required
def photo_upload(request, album_id):
    """\
    Uploads a Photo.

    This reads the image metadata from the file on the filesystem into the
    corresponding properties in the Photo object.

    It is assumed that no Photo properties associated with the image metadata
    are submitted, as this would overwrite the metadata in the file without
    informing the user of previous values.

    """
    if request.method == 'POST':
        album = get_object_or_404(Album, pk=album_id)
        form = PhotoUploadForm(request.POST, request.FILES)

        if form.is_valid():
            photo = form.cleaned_data['image']

            new_photo = form.save(commit=False)
            new_photo.owner = request.user
            new_photo.album = album

            photo.open()
            image = Image.open(photo)
            if image.format == 'JPEG':
                new_photo.is_jpeg = True
            photo.close()

            new_photo.save()
            form.save_m2m()
            new_photo.create_thumbnail()
            new_photo.sync_metadata_from_file()

            request.user.message_set.create(
                message="Your photograph was added successfully.")
            return HttpResponseRedirect(reverse("photo_in_album", kwargs={
                "object_id": form.instance.id,
            }))
    else:
        album_count = Album.objects.filter(pk=album_id).count()
        if not album_count > 0:
            raise Http404
        form = PhotoUploadForm()

    return render_to_response('photos/photo_upload.html', {
        'form': form,
        'album_id': album_id,
    })


@login_required
def photo_edit(request, object_id, **kwargs):
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
            url = reverse("photo_detail", args=[object_id])
            if "in_album" in kwargs:
                url = reverse("photo_in_album", kwargs={
                    "object_id": object_id,
                })
            return HttpResponseRedirect(url)

    else:
        object = get_object_or_404(Photo, pk=object_id)
        form = PhotoEditForm(instance=object)

    return render_to_response('photos/photo_edit.html', {
        'form': form,
    })


# TODO: Change name to new_album.
@login_required
def create_album(request):
    """\
    Creates an album.

    """
    if request.method == 'POST':
        form = AlbumCreationForm(request.POST, request.FILES)

        if form.is_valid():
            new_album = form.save(commit=False)
            new_album.owner = request.user

            new_album.save()
            form.save_m2m()

            request.user.message_set.create(
                message="Your album was created successfully.")
            return HttpResponseRedirect(reverse("album_detail",
                                                args=[form.instance.id]))
    else:
        form = AlbumCreationForm()

    return render_to_response('photos/album_creation.html', {
        'form': form,
    })
