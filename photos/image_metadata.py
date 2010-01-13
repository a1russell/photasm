from datetime import datetime

import pyexiv2


def get_image_width_key(img_is_jpeg):
    if img_is_jpeg:
        return 'Exif.Photo.PixelXDimension'
    return 'Exif.Image.ImageWidth'


def get_image_height_key(img_is_jpeg):
    if img_is_jpeg:
        return 'Exif.Photo.PixelYDimension'
    return 'Exif.Image.ImageLength'


def require_pyexiv2_obj(obj, obj_name):
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
    try:
        iter(obj)
    except TypeError:
        pass
    else:
        if not isinstance(obj, str):
            return True
    return False


def _collapse_empty_to_none(value):
    try:
        value_length = len(value)
    except TypeError:
        pass
    else:
        if value_length == 0:
            value = None
    return value


def _del_img_key(image, metadata_key):
    # Workaround for a bug in pyexiv2:
    # https://bugs.launchpad.net/pyexiv2/+bug/343403
    try:
        del image[metadata_key]
    except (KeyError, TypeError):
        pass


def _metadata_value_synced_with_file(value, image, metadata_key, keys_method):
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
    return _metadata_value_synced_with_file(value, image, metadata_key,
                                            pyexiv2.Image.exifKeys)


def value_synced_with_iptc(value, image, metadata_key):
    return _metadata_value_synced_with_file(value, image, metadata_key,
                                            pyexiv2.Image.iptcKeys)


def value_synced_with_exif_and_iptc(value, image, exif_key, iptc_key):
    require_pyexiv2_obj(image, 'image')
    exif_value = None
    iptc_value = None
    
    if exif_key in image.exifKeys():
        exif_value = image[exif_key]
    if iptc_key in image.iptcKeys():
        iptc_value = image[iptc_key]
    
    # Empty set or string counts as in sync with None.
    value = _collapse_empty_to_none(value)
    
    # If values are iterable, they should not be considered out of sync if
    # they simply aren't sorted the same. Therefore, iterable values are
    # converted to unordered sets.
    if _is_iter(value):
        value = set(value)
    if _is_iter(exif_value):
        exif_value = set(exif_value)
    if _is_iter(iptc_value):
        iptc_value = set(iptc_value)
    
    if exif_value is None:
        return value == iptc_value
    if iptc_value is None:
        return value == exif_value
    return value == exif_value == iptc_value


def datetime_synced_with_exif_and_iptc(datetime_value, image,
                                       exif_datetime_key,
                                       iptc_date_key, iptc_time_key):
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
    
    if iptc_date_value and iptc_time_value:
        iptc_datetime_value = datetime.combine(iptc_date_value,
                                               iptc_time_value)
    
    if exif_datetime_value is None:
        return datetime_value == iptc_datetime_value
    if iptc_datetime_value is None:
        return datetime_value == exif_datetime_value
    return datetime_value == exif_datetime_value == iptc_datetime_value


def _sync_metadata_value_to_file(value, image, metadata_key, sync_check_func):
    require_pyexiv2_obj(image, 'image')
    
    value_deleted = False
    mod = not sync_check_func(value, image, metadata_key)
    if mod:
        # If value is empty or None, delete key.
        if value is None:
            _del_img_key(image, metadata_key)
            value_deleted = True
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
    return _sync_metadata_value_to_file(value, image, metadata_key,
                                        value_synced_with_exif)


def sync_value_to_iptc(value, image, metadata_key):
    return _sync_metadata_value_to_file(value, image, metadata_key,
                                        value_synced_with_iptc)


def sync_value_to_exif_and_iptc(value, image, exif_key, iptc_key):
    require_pyexiv2_obj(image, 'image')
    
    value_deleted = False
    mod = not value_synced_with_exif_and_iptc(value, image, exif_key, iptc_key)
    if mod:
        # If value is empty or None, delete Exif key.
        if value is None:
            _del_img_key(image, exif_key)
            value_deleted = True
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
