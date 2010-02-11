from datetime import datetime

import pyexiv2


def get_image_width_key(img_is_jpeg):
    """\
    Returns appropriate Exif key related to an image's X-resolution (width).
    
    Parameters:
    img_is_jpeg -- whether or not the image is a JPEG
    
    """
    if img_is_jpeg:
        return 'Exif.Photo.PixelXDimension'
    return 'Exif.Image.ImageWidth'


def get_image_height_key(img_is_jpeg):
    """\
    Returns appropriate Exif key related to an image's Y-resolution (height).
    
    Parameters:
    img_is_jpeg -- whether or not the image is a JPEG
    
    """
    if img_is_jpeg:
        return 'Exif.Photo.PixelYDimension'
    return 'Exif.Image.ImageLength'


def require_pyexiv2_obj(obj, obj_name):
    """\
    Ensures that a given object is a valid pyexiv2.Image.
    
    Parameters:
    obj -- object to type-check
    obj_name -- variable name of the object
    
    """
    is_pyexiv2_obj = True
    if (not (hasattr(obj, '__getitem__') and callable(obj.__getitem__) and
        hasattr(obj, '__setitem__') and callable(obj.__setitem__) and
        hasattr(obj, '__delitem__') and callable(obj.__delitem__) and
        hasattr(obj, 'exifKeys') and callable(obj.exifKeys) and
        hasattr(obj, 'iptcKeys') and callable(obj.iptcKeys))):
        is_pyexiv2_obj = False
    
    if not is_pyexiv2_obj:
        raise TypeError("Object '%s' must be an instance of pyexiv2.Image."
                        % (obj_name,))


def _is_iter(obj):
    """\
    Checks to see if an object is iterable.
    
    Iterable types include lists, sets, etc. In this case, strings do not
    count.
    
    Returns True if the object is iterable; False otherwise.
    
    Parameters:
    obj -- object to type-check
    
    """
    try:
        iter(obj)
    except TypeError:
        pass
    else:
        if not isinstance(obj, str):
            return True
    return False


def _collapse_empty_to_none(value):
    """\
    Collapses an value of zero length to None.
    
    In other words, this function takes a value and tries to see if it has a
    length. If it does, and that length is zero, this function returns None.
    Otherwise, it returns the original value.
    
    Parameters:
    value -- value for which to collapse to None if zero-length
    
    """
    try:
        value_length = len(value)
    except TypeError:
        pass
    else:
        if value_length == 0:
            value = None
    return value


def _del_img_key(image, metadata_key):
    """\
    Deletes an image metadata tag for a specified key.
    
    Parameters:
    metadata_key -- key of the metadata tag to delete
    
    """
    # Workaround for a bug in pyexiv2:
    # https://bugs.launchpad.net/pyexiv2/+bug/343403
    try:
        del image[metadata_key]
    except TypeError:
        image[metadata_key] = None
    except KeyError:
        pass


def _metadata_value_synced_with_file(value, image, metadata_key, keys_method):
    """\
    Determines whether a value is in sync with metadata in an image file.
    
    Returns True if the metadata is sychronized; False otherwise.
    
    Parameters:
    value -- value of the metadata property to check
    image -- pyexiv2.Image object containing metadata to compare against
    metadata_key -- key of the metadata tag for which to compare
    keys_method -- method to retrieve appropriate list of keys that could
                   contain metadata_key
    
    """
    require_pyexiv2_obj(image, 'image')
    metadata_value = None
    
    if metadata_key in keys_method(image):
        metadata_value = image[metadata_key]
    
    # Empty set or string counts as in sync with None.
    value = _collapse_empty_to_none(value)
    
    # If values are iterable, they should not be considered out of sync if
    # they simply aren't sorted the same. Therefore, iterable values are
    # converted to unordered sets.
    if _is_iter(value):
        value = set(value)
    if _is_iter(metadata_value):
        metadata_value = set(metadata_value)
    
    return value == metadata_value


def value_synced_with_exif(value, image, metadata_key):
    """\
    Determines whether a value is in sync with Exif metadata in an image file.
    
    Returns True if the metadata is sychronized; False otherwise.
    
    Parameters:
    value -- value of the metadata property to check
    image -- pyexiv2.Image object containing metadata to compare against
    metadata_key -- key of the Exif metadata tag for which to compare
    
    """
    return _metadata_value_synced_with_file(value, image, metadata_key,
                                            pyexiv2.Image.exifKeys)


def value_synced_with_iptc(value, image, metadata_key):
    """\
    Determines whether a value is in sync with IPTC metadata in an image file.
    
    Returns True if the metadata is sychronized; False otherwise.
    
    Parameters:
    value -- value of the metadata property to check
    image -- pyexiv2.Image object containing metadata to compare against
    metadata_key -- key of the IPTC metadata tag for which to compare
    
    """
    return _metadata_value_synced_with_file(value, image, metadata_key,
                                            pyexiv2.Image.iptcKeys)


def value_synced_with_exif_and_iptc(value, image, exif_key, iptc_key):
    """\
    Determines whether a value is in sync with metadata in an image file.
    
    Both Exif and IPTC tags are checked.
    
    Returns True if the metadata is sychronized; False otherwise.
    
    Parameters:
    value -- value of the metadata property to check
    image -- pyexiv2.Image object containing metadata to compare against
    exif_key -- key of the Exif metadata tag for which to compare
    iptc_key -- key of the IPTC metadata tag for which to compare
    
    """
    require_pyexiv2_obj(image, 'image')
    exif_value = None
    iptc_value = None
    
    if exif_key in image.exifKeys():
        exif_value = image[exif_key]
    if iptc_key in image.iptcKeys():
        iptc_value = image[iptc_key]
    
    # Empty set or string counts as in sync with None.
    value = _collapse_empty_to_none(value)
    
    if exif_value is None:
        return value == iptc_value
    if iptc_value is None:
        return value == exif_value
    return value == exif_value == iptc_value


def datetime_synced_with_exif_and_iptc(datetime_value, image,
                                       exif_datetime_key,
                                       iptc_date_key, iptc_time_key):
    """\
    Determines whether a date/time value is in sync with image file metadata.
    
    Both Exif and IPTC tags are checked. Note that Exif stores combined
    date/time values in a single tag, while IPTC separates the date value into
    one tag and the time value into another.
    
    Returns True if the metadata is sychronized; False otherwise.
    
    Parameters:
    datetime_value -- date/time value of the metadata property to check
    image -- pyexiv2.Image object containing metadata to compare against
    exif_datetime_key -- key of Exif date/time metadata to compare against
    iptc_date_key -- key of the IPTC date metadata tag to compare against
    iptc_time_key -- key of the IPTC time metadata tag to compare against
    
    """
    require_pyexiv2_obj(image, 'image')
    exif_datetime_value = None
    iptc_date_value = None
    iptc_time_value = None
    iptc_datetime_value = None
    
    try:
        datetime_value = datetime_value.replace(microsecond=0, tzinfo=None)
    except AttributeError:
        # datetime_value was probably None
        pass
    
    if exif_datetime_key in image.exifKeys():
        exif_datetime_value = image[exif_datetime_key]
    if iptc_date_key in image.iptcKeys():
        iptc_date_value = image[iptc_date_key]
    if iptc_time_key in image.iptcKeys():
        iptc_time_value = image[iptc_time_key]
        iptc_time_value = iptc_time_value.replace(tzinfo=None)
    
    if iptc_date_value and iptc_time_value:
        iptc_datetime_value = datetime.combine(iptc_date_value,
                                               iptc_time_value)
    
    if exif_datetime_value is None:
        return datetime_value == iptc_datetime_value
    if iptc_datetime_value is None:
        return datetime_value == exif_datetime_value
    return datetime_value == exif_datetime_value == iptc_datetime_value


def _sync_metadata_value_to_file(value, image, metadata_key, sync_check_func):
    """\
    Writes image metadata to a file.
    
    Metadata is only actually written to the files if the values are
    out of sync.
    
    Returns True if metadata needed to be written to the file;
    False otherwise.
    
    Parameters:
    value -- value of the metadata property to synchronize
    image -- pyexiv2.Image object containing metadata to synchronize
    metadata_key -- key of the metadata tag to synchronize
    sync_check_func -- function to determine sync status of metadata tag
    
    """
    require_pyexiv2_obj(image, 'image')
    
    value_deleted = False
    mod = not sync_check_func(value, image, metadata_key)
    if mod:
        # If value is empty or None, delete key.
        if value is None:
            _del_img_key(image, metadata_key)
            value_deleted = True
        else:
            try:
                value_length = len(value)
            except TypeError:
                pass
            else:
                if value_length == 0:
                    _del_img_key(image, metadata_key)
                    value_deleted = True
        
        # Otherwise, save key.
        if not value_deleted:
            image[metadata_key] = value
    
    return mod


def sync_value_to_exif(value, image, metadata_key):
    """\
    Writes Exif image metadata to a file.
    
    Metadata is only actually written to the files if the values are
    out of sync.
    
    Returns True if metadata needed to be written to the file;
    False otherwise.
    
    Parameters:
    value -- value of the metadata property to synchronize
    image -- pyexiv2.Image object containing metadata to synchronize
    metadata_key -- key of the Exif metadata tag to synchronize
    
    """
    return _sync_metadata_value_to_file(value, image, metadata_key,
                                        value_synced_with_exif)


def sync_value_to_iptc(value, image, metadata_key):
    """\
    Writes IPTC image metadata to a file.
    
    Metadata is only actually written to the files if the values are
    out of sync.
    
    Returns True if metadata needed to be written to the file;
    False otherwise.
    
    Parameters:
    value -- value of the metadata property to synchronize
    image -- pyexiv2.Image object containing metadata to synchronize
    metadata_key -- key of the IPTC metadata tag to synchronize
    
    """
    return _sync_metadata_value_to_file(value, image, metadata_key,
                                        value_synced_with_iptc)


def sync_value_to_exif_and_iptc(value, image, exif_key, iptc_key):
    """\
    Writes Exif and IPTC image metadata to a file.
    
    Metadata is only actually written to the files if the values are
    out of sync.
    
    Returns True if metadata needed to be written to the file;
    False otherwise.
    
    Parameters:
    value -- value of the metadata property to synchronize
    image -- pyexiv2.Image object containing metadata to synchronize
    exif_key -- key of the Exif metadata tag to synchronize
    iptc_key -- key of the IPTC metadata tag to synchronize
    
    """
    require_pyexiv2_obj(image, 'image')
    
    value_deleted = False
    mod = not value_synced_with_exif_and_iptc(value, image, exif_key, iptc_key)
    if mod:
        # If value is empty or None, delete Exif key.
        if value is None:
            _del_img_key(image, exif_key)
            value_deleted = True
        else:
            try:
                value_length = len(value)
            except TypeError:
                pass
            else:
                if value_length == 0:
                    _del_img_key(image, exif_key)
                    value_deleted = True
        
        # Otherwise, save Exif key.
        if not value_deleted:
            image[exif_key] = value
        
        # Delete IPTC key.
        if iptc_key in image.iptcKeys():
            _del_img_key(image, iptc_key)
    
    return mod


def sync_datetime_to_exif_and_iptc(datetime_value, image, exif_datetime_key,
                                   iptc_date_key, iptc_time_key):
    """\
    Writes Exif and IPTC date/time image metadata to a file.
    
    Note that Exif stores combined date/time values in a single tag, while IPTC
    separates the date value into one tag and the time value into another.
    
    Metadata is only actually written to the files if the values are
    out of sync.
    
    Returns True if metadata needed to be written to the file;
    False otherwise.
    
    Parameters:
    datetime_value -- date/time value of the metadata property to synchronize
    image -- pyexiv2.Image object containing metadata to synchronize
    exif_datetime_key -- key of Exif date/time metadata to synchronize
    iptc_date_key -- key of the IPTC date metadata tag to synchronize
    iptc_time_key -- key of the IPTC time metadata tag to synchronize
    
    """
    require_pyexiv2_obj(image, 'image')
    
    mod = not datetime_synced_with_exif_and_iptc(datetime_value, image,
                                                 exif_datetime_key,
                                                 iptc_date_key, iptc_time_key)
    if mod:
        if datetime_value is not None:
            image[exif_datetime_key] = datetime_value
        else:
            _del_img_key(image, exif_datetime_key)
        
        # Delete IPTC keys.
        if iptc_date_key in image.iptcKeys():
            _del_img_key(image, iptc_date_key)
        if iptc_time_key in image.iptcKeys():
            _del_img_key(image, iptc_time_key)
    
    return mod


def read_value_from_exif_and_iptc(image, exif_key, iptc_key):
    """\
    Reads image metadata value with overlapping Exif and IPTC tags from a file.
    
    Returns the metadata value from the file according to the recommendations
    given by the Metadata Working Group.
    
    Parameters:
    image -- pyexiv2.Image object containing metadata to read
    exif_key -- key of the Exif metadata tag to read
    iptc_key -- key of the IPTC metadata tag to read
    
    """
    require_pyexiv2_obj(image, 'image')
    exif_value = None
    iptc_value = None
    
    if exif_key in image.exifKeys():
        exif_value = image[exif_key]
    if iptc_key in image.iptcKeys():
        iptc_value = image[iptc_key]
    
    if exif_value is None:
        return iptc_value
    return exif_value


def read_datetime_from_exif_and_iptc(image, exif_datetime_key,
                                     iptc_date_key, iptc_time_key):
    """\
    Reads image metadata date/time value with overlapping Exif and IPTC tags.
    
    Note that Exif stores combined date/time values in a single tag, while IPTC
    separates the date value into one tag and the time value into another.
    
    Returns the metadata value from the file according to the recommendations
    given by the Metadata Working Group.
    
    Parameters:
    image -- pyexiv2.Image object containing metadata to read
    exif_datetime_key -- key of Exif metadata tag to read
    iptc_date_key -- key of the IPTC date metadata tag to read
    iptc_time_key -- key of the IPTC time metadata tag to read
    
    """
    require_pyexiv2_obj(image, 'image')
    exif_datetime_value = None
    iptc_date_value = None
    iptc_time_value = None
    iptc_datetime_value = None
    
    if exif_datetime_key in image.exifKeys():
        exif_datetime_value = image[exif_datetime_key]
    if iptc_date_key in image.iptcKeys():
        iptc_date_value = image[iptc_date_key]
    if iptc_time_key in image.iptcKeys():
        iptc_time_value = image[iptc_time_key]
        iptc_time_value = iptc_time_value.replace(tzinfo=None)
    
    if exif_datetime_value is None:
        if iptc_date_value and iptc_time_value:
            iptc_datetime_value = datetime.combine(iptc_date_value,
                                                   iptc_time_value)
        return iptc_datetime_value
    return exif_datetime_value

