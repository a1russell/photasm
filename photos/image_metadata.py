import pyexiv2


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


def _metadata_value_synced_with_file(value, image, metadata_key, keys_method):
    require_pyexiv2_obj(image, 'image')
    metadata_value = None
    
    if metadata_key in keys_method(image):
        metadata_value = image[metadata_key]
    
    # If values are iterable, they should not be considered out of sync if
    # they simply aren't sorted the same. Therefore, iterable values are
    # converted to unordered sets.
    try:
        iter(value)
    except TypeError:
        pass
    else:
        value = set(value)
    try:
        iter(metadata_value)
    except TypeError:
        pass
    else:
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
    
    # If values are iterable, they should not be considered out of sync if
    # they simply aren't sorted the same. Therefore, iterable values are
    # converted to unordered sets.
    try:
        iter(value)
    except TypeError:
        pass
    else:
        value = set(value)
    try:
        iter(exif_value)
    except TypeError:
        pass
    else:
        exif_value = set(exif_value)
    try:
        iter(iptc_value)
    except TypeError:
        pass
    else:
        iptc_value = set(iptc_value)
    
    if exif_value is None:
        return value == iptc_value
    if iptc_value is None:
        return value == exif_value
    return value == exif_value == iptc_value


def _sync_metadata_value_to_file(value, image, metadata_key, sync_check_func):
    require_pyexiv2_obj(image, 'image')
    
    mod = not sync_check_func(value, image, metadata_key)
    if mod:
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
    
    mod = not value_synced_with_exif_and_iptc(value, image, exif_key, iptc_key)
    if mod:
        image[exif_key] = value
        if iptc_key in image.iptcKeys():
            try:
                del image[iptc_key]
            # Workaround for a bug in pyexiv2:
            # https://bugs.launchpad.net/pyexiv2/+bug/343403
            except KeyError:
                pass
    
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
