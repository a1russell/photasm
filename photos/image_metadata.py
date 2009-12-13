import pyexiv2


def _value_synced_with_metadata(value, path, metadata_key, keys_method):
    image_metadata = pyexiv2.Image(path)
    image_metadata.readMetadata()
    metadata_value = None
    
    if metadata_key in keys_method(image_metadata):
        metadata_value = image_metadata[metadata_key]
    
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
    
    if metadata_value is None:
        return False
    return value == metadata_value


def value_synced_with_exif(value, path, metadata_key):
    return _value_synced_with_metadata(value, path, metadata_key,
                                       pyexiv2.Image.exifKeys)


def value_synced_with_iptc(value, path, metadata_key):
    return _value_synced_with_metadata(value, path, metadata_key,
                                       pyexiv2.Image.iptcKeys)


def value_synced_with_exif_and_iptc(value, path, exif_key, iptc_key):
    image_metadata = pyexiv2.Image(path)
    image_metadata.readMetadata()
    exif_value = None
    iptc_value = None
    
    if exif_key in image_metadata.exifKeys():
        exif_value = image_metadata[exif_key]
    if iptc_key in image_metadata.iptcKeys():
        iptc_value = image_metadata[iptc_key]
    
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
    
    if exif_value is None and iptc_value is None:
        return False
    if exif_value is None:
        return value == iptc_value
    if iptc_value is None:
        return value == exif_value
    return value == exif_value == iptc_value
