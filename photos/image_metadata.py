import pyexiv2


def _value_synced_with_metadata(value, path, metadata_key, keys_method):
    image_metadata = pyexiv2.Image(path)
    image_metadata.readMetadata()
    metadata_value = None
    
    if metadata_key in keys_method(image_metadata):
        metadata_value = image_metadata(metadata_key)
    
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
        exif_value = image_metadata(exif_key)
    if iptc_key in image_metadata.iptcKeys():
        iptc_value = image_metadata(iptc_key)
    
    if exif_value is None and iptc_value is None:
        return False
    if exif_value is None:
        return value == iptc_value
    if iptc_value is None:
        return value == exif_value
    return value == exif_value == iptc_value
