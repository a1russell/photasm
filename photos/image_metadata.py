from datetime import datetime

import pyexiv2


def get_image_width_key(img_is_jpeg):
    """\
    Returns appropriate Exif key related to an image's X-resolution (width).
    
    Parameters:
    img_is_jpeg -- whether or not the image is a JPEG
    
    >>> img_is_jpeg = True
    >>> print get_image_width_key(img_is_jpeg)
    Exif.Photo.PixelXDimension
    
    >>> img_is_jpeg = False
    >>> print get_image_width_key(img_is_jpeg)
    Exif.Image.ImageWidth
    
    """
    if img_is_jpeg:
        return 'Exif.Photo.PixelXDimension'
    return 'Exif.Image.ImageWidth'


def get_image_height_key(img_is_jpeg):
    """\
    Returns appropriate Exif key related to an image's Y-resolution (height).
    
    Parameters:
    img_is_jpeg -- whether or not the image is a JPEG
    
    >>> img_is_jpeg = True
    >>> print get_image_height_key(img_is_jpeg)
    Exif.Photo.PixelYDimension
    
    >>> img_is_jpeg = False
    >>> print get_image_height_key(img_is_jpeg)
    Exif.Image.ImageLength
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    
    >>> # Use this function.
    >>> print require_pyexiv2_obj(metadata, 'metadata')
    None
    >>> test_obj = "This isn't a valid pyexiv2.Image."
    >>> print require_pyexiv2_obj(test_obj, 'test_obj')
    Traceback (most recent call last):
        ...
    TypeError: Object 'test_obj' must be an instance of pyexiv2.Image.
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> print _is_iter(set())
    True
    
    >>> print _is_iter("Test string.")
    False
    
    >>> print _is_iter(1)
    False
    
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
    
    >>> print _collapse_empty_to_none([])
    None
    
    >>> print _collapse_empty_to_none([1, 2, 3])
    [1, 2, 3]
    
    >>> print _collapse_empty_to_none(1)
    1
    
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
    
    >>> # Set things up.
    >>> import datetime
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    
    >>> # Use this function.
    >>> value = 'Test file with description'
    >>> metadata['Exif.Image.ImageDescription'] = value
    >>> metadata.writeMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    >>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    
    >>> value = 'Test file with description'
    >>> metadata['Iptc.Application2.Caption'] = value
    >>> metadata.writeMetadata()
    >>> _del_img_key(metadata, 'Iptc.Application2.Caption')
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    
    >>> value = datetime.date.today()
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = value
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
    True
    >>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> test_description = 'Test file with description'
    >>> metadata['Exif.Image.ImageDescription'] = test_description
    >>> metadata.writeMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    
    >>> # Use this function.
    >>> print _metadata_value_synced_with_file(test_description, metadata,
    ...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
    True
    
    >>> test_description = 'New, different test description'
    >>> print _metadata_value_synced_with_file(test_description, metadata,
    ...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
    False
    
    >>> del metadata['Exif.Image.ImageDescription']
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> empty_string = ""
    >>> print _metadata_value_synced_with_file(empty_string, metadata,
    ...     'Exif.Image.ImageDescription', pyexiv2.Image.exifKeys)
    True
    
    >>> keywords = ['c', 'a', 'b']
    >>> metadata['Iptc.Application2.Keywords'] = keywords
    >>> metadata.writeMetadata()
    >>> keywords.sort()
    >>> print keywords
    ['a', 'b', 'c']
    >>> print _metadata_value_synced_with_file(keywords, metadata,
    ...     'Iptc.Application2.Keywords', pyexiv2.Image.iptcKeys)
    True
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> test_description = 'Test file with description'
    >>> metadata['Exif.Image.ImageDescription'] = test_description
    >>> metadata.writeMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    
    >>> # Use this function.
    >>> print value_synced_with_exif(test_description, metadata,
    ...                              'Exif.Image.ImageDescription')
    True
    
    >>> test_description = 'New, different test description'
    >>> print value_synced_with_exif(test_description, metadata,
    ...                              'Exif.Image.ImageDescription')
    False
    
    >>> del metadata['Exif.Image.ImageDescription']
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> empty_string = ""
    >>> print value_synced_with_exif(empty_string, metadata,
    ...                              'Exif.Image.ImageDescription')
    True
    >>> none_argument = None
    >>> print value_synced_with_exif(none_argument, metadata,
    ...                              'Exif.Image.ImageDescription')
    True
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> test_keywords = ['IPTC', 'test', 'keywords']
    >>> metadata['Iptc.Application2.Keywords'] = test_keywords
    >>> metadata.writeMetadata()
    >>> print metadata['Iptc.Application2.Keywords']
    ('IPTC', 'test', 'keywords')
    
    >>> # Use this function.
    >>> print value_synced_with_iptc(test_keywords, metadata,
    ...                              'Iptc.Application2.Keywords')
    True
    
    >>> test_keywords.append('modified')
    >>> print value_synced_with_iptc(test_keywords, metadata,
    ...                              'Iptc.Application2.Keywords')
    False
    
    >>> _del_img_key(metadata, 'Iptc.Application2.Keywords')
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.Keywords' in metadata.iptcKeys()
    False
    >>> empty_list = []
    >>> print value_synced_with_iptc(empty_list, metadata,
    ...                              'Iptc.Application2.Keywords')
    True
    >>> none_argument = None
    >>> print value_synced_with_iptc(none_argument, metadata,
    ...                              'Iptc.Application2.Keywords')
    True
    
    >>> test_keywords = ['c', 'a', 'b']
    >>> metadata['Iptc.Application2.Keywords'] = test_keywords
    >>> metadata.writeMetadata()
    >>> test_keywords.sort()
    >>> print test_keywords
    ['a', 'b', 'c']
    >>> print value_synced_with_iptc(test_keywords, metadata,
    ...                              'Iptc.Application2.Keywords')
    True
    
    >>> empty_string = ""
    >>> print value_synced_with_iptc(empty_string, metadata,
    ...                              'Iptc.Application2.Caption')
    True
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> test_description = 'Test file with description'
    >>> metadata['Exif.Image.ImageDescription'] = test_description
    >>> metadata['Iptc.Application2.Caption'] = test_description
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    >>> print metadata['Iptc.Application2.Caption']
    Test file with description
    
    >>> # Use this function.
    >>> print value_synced_with_exif_and_iptc(test_description, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    True
    
    >>> test_description = 'New, different test description'
    >>> print value_synced_with_exif_and_iptc(test_description, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    False
    
    >>> test_description = metadata['Exif.Image.ImageDescription']
    >>> metadata['Exif.Image.ImageDescription'] = 'modified'
    >>> metadata.writeMetadata()
    >>> print value_synced_with_exif_and_iptc(test_description, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    False
    
    >>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> print value_synced_with_exif_and_iptc(test_description, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.Caption')
    >>> metadata['Exif.Image.ImageDescription'] = test_description
    >>> metadata.writeMetadata()
    >>> print value_synced_with_exif_and_iptc(test_description, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    True
    
    >>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    >>> empty_string = ""
    >>> print value_synced_with_exif_and_iptc(empty_string, metadata,
    ...     'Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    True
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import datetime
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> value = datetime.datetime.now()
    >>> time_keys = ('Exif.Photo.DateTimeOriginal',
    ...              'Iptc.Application2.DateCreated',
    ...              'Iptc.Application2.TimeCreated',)
    >>> metadata['Exif.Photo.DateTimeOriginal'] = value
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = value.date()
    ... except TypeError:
    ...     pass
    >>> try:
    ...     metadata['Iptc.Application2.TimeCreated'] = value.time()
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    
    >>> # Use this function.
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    True
    
    >>> one_second = datetime.timedelta(seconds=1)
    >>> value = value + one_second
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    False
    
    >>> value = metadata['Exif.Photo.DateTimeOriginal']
    >>> metadata['Exif.Photo.DateTimeOriginal'] =  value + one_second
    >>> metadata.writeMetadata()
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    False
    
    >>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
    >>> metadata.writeMetadata()
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
    >>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
    >>> metadata['Exif.Photo.DateTimeOriginal'] = value
    >>> metadata.writeMetadata()
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    True
    
    >>> value = None
    >>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
    >>> metadata.writeMetadata()
    >>> print datetime_synced_with_exif_and_iptc(value, metadata, *time_keys)
    True
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    
    >>> # Use this function.
    >>> test_description = 'Test file with description'
    >>> print _sync_metadata_value_to_file(test_description, metadata,
    ...     'Exif.Image.ImageDescription', value_synced_with_exif)
    True
    >>> metadata.writeMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    >>> print _sync_metadata_value_to_file(test_description, metadata,
    ...     'Exif.Image.ImageDescription', value_synced_with_exif)
    False
    
    >>> empty_string = ''
    >>> print _sync_metadata_value_to_file(empty_string, metadata,
    ...     'Exif.Image.ImageDescription', value_synced_with_exif)
    True
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> print _sync_metadata_value_to_file(empty_string, metadata,
    ...     'Exif.Image.ImageDescription', value_synced_with_exif)
    False
    
    >>> none_argument = None
    >>> print 'Exif.Image.Orientation' in metadata.exifKeys()
    False
    >>> print _sync_metadata_value_to_file(none_argument, metadata,
    ...     'Exif.Image.Orientation', value_synced_with_exif)
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    
    >>> # Use this function.
    >>> test_description = 'Test file with description'
    >>> print sync_value_to_exif(test_description, metadata,
    ...                          'Exif.Image.ImageDescription')
    True
    >>> metadata.writeMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    >>> print sync_value_to_exif(test_description, metadata,
    ...                          'Exif.Image.ImageDescription')
    False
    
    >>> empty_string = ''
    >>> print sync_value_to_exif(empty_string, metadata,
    ...                          'Exif.Image.ImageDescription')
    True
    >>> metadata.writeMetadata()
    >>> print 'Exif.Image.ImageDescription' in metadata.exifKeys()
    False
    >>> print sync_value_to_exif(empty_string, metadata,
    ...                          'Exif.Image.ImageDescription')
    False
    
    >>> none_argument = None
    >>> print 'Exif.Image.Orientation' in metadata.exifKeys()
    False
    >>> print sync_value_to_exif(none_argument, metadata,
    ...                          'Exif.Image.Orientation')
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    
    >>> # Use this function.
    >>> test_description = 'Test file with description'
    >>> print sync_value_to_iptc(test_description, metadata,
    ...                          'Iptc.Application2.Caption')
    True
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print metadata['Iptc.Application2.Caption']
    Test file with description
    >>> print sync_value_to_iptc(test_description, metadata,
    ...                          'Iptc.Application2.Caption')
    False
    
    >>> empty_string = ""
    >>> print sync_value_to_iptc(empty_string, metadata,
    ...                          'Iptc.Application2.Caption')
    True
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    >>> print sync_value_to_iptc(empty_string, metadata,
    ...                          'Iptc.Application2.Caption')
    False
    
    >>> test_keywords = ['IPTC', 'test', 'keywords']
    >>> print sync_value_to_iptc(test_keywords, metadata,
    ...                          'Iptc.Application2.Keywords')
    True
    >>> metadata.writeMetadata()
    >>> print metadata['Iptc.Application2.Keywords']
    ('IPTC', 'test', 'keywords')
    
    >>> empty_list = []
    >>> print sync_value_to_iptc(empty_list, metadata,
    ...                          'Iptc.Application2.Keywords')
    True
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.Keywords' in metadata.iptcKeys()
    False
    >>> print sync_value_to_iptc(empty_list, metadata,
    ...                          'Iptc.Application2.Keywords')
    False
    
    >>> none_argument = None
    >>> print 'Iptc.Envelope.ARMId' in metadata.iptcKeys()
    False
    >>> print sync_value_to_iptc(none_argument, metadata,
    ...                          'Iptc.Application2.DateCreated')
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    
    >>> # Use this function.
    >>> test_description = 'Test file with description'
    >>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    Test file with description
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    >>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
    False
    >>> metadata['Iptc.Application2.Caption'] = test_description
    >>> del metadata['Exif.Image.ImageDescription']
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
    False
    
    >>> test_description = 'File with NEW description'
    >>> print sync_value_to_exif_and_iptc(test_description, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print metadata['Exif.Image.ImageDescription']
    File with NEW description
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    
    >>> empty_string = ""
    >>> print sync_value_to_exif_and_iptc(empty_string, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> print 'Iptc.Application2.Caption' in metadata.iptcKeys()
    False
    >>> print sync_value_to_exif_and_iptc(empty_string, metadata, *keys)
    False
    
    >>> none_argument = None
    >>> print sync_value_to_exif_and_iptc(none_argument, metadata, *keys)
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import datetime
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> keys = ('Exif.Photo.DateTimeOriginal',
    ...         'Iptc.Application2.DateCreated',
    ...         'Iptc.Application2.TimeCreated',)
    
    >>> # Use this function.
    >>> value = datetime.datetime.now()
    >>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> # Metadata doesn't have microsecond precision.
    >>> value_no_us = value.replace(microsecond=0)
    >>> print metadata['Exif.Photo.DateTimeOriginal'] == value_no_us
    True
    >>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
    False
    >>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
    False
    >>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
    False
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = value.date()
    ... except TypeError:
    ...     pass
    >>> try:
    ...     metadata['Iptc.Application2.TimeCreated'] = value.time()
    ... except TypeError:
    ...     pass
    >>> del metadata['Exif.Photo.DateTimeOriginal']
    >>> metadata.writeMetadata()
    >>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
    False
    
    >>> one_second = datetime.timedelta(seconds=1)
    >>> value += one_second
    >>> print sync_datetime_to_exif_and_iptc(value, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> value_no_us = value.replace(microsecond=0)
    >>> print metadata['Exif.Photo.DateTimeOriginal'] == value_no_us
    True
    >>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
    False
    >>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
    False
    
    >>> none_argument = None
    >>> print sync_datetime_to_exif_and_iptc(none_argument, metadata, *keys)
    True
    >>> metadata.writeMetadata()
    >>> print 'Exif.Photo.DateTimeOriginal' in metadata.exifKeys()
    False
    >>> print 'Iptc.Application2.DateCreated' in metadata.iptcKeys()
    False
    >>> print 'Iptc.Application2.TimeCreated' in metadata.iptcKeys()
    False
    >>> print sync_datetime_to_exif_and_iptc(none_argument, metadata, *keys)
    False
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> keys = ('Exif.Image.ImageDescription', 'Iptc.Application2.Caption')
    >>> exif_val = 'Test file with Exif description tag'
    >>> iptc_val = 'Test file with IPTC description tag'
    
    >>> # Use this function
    >>> metadata['Exif.Image.ImageDescription'] = exif_val
    >>> metadata['Iptc.Application2.Caption'] = iptc_val
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print read_value_from_exif_and_iptc(metadata, *keys) == exif_val
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.Caption')
    >>> metadata.writeMetadata()
    >>> print read_value_from_exif_and_iptc(metadata, *keys) == exif_val
    True
    
    >>> _del_img_key(metadata, 'Exif.Image.ImageDescription')
    >>> metadata['Iptc.Application2.Caption'] = iptc_val
    >>> metadata.writeMetadata()
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> print read_value_from_exif_and_iptc(metadata, *keys) == iptc_val
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.Caption')
    >>> metadata.writeMetadata()
    >>> print read_value_from_exif_and_iptc(metadata, *keys)
    None
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
    
    >>> # Set things up.
    >>> import datetime
    >>> import os
    >>> import tempfile
    >>> from PIL import Image
    >>> import pyexiv2
    >>> file_descriptor, file_path = tempfile.mkstemp(suffix='.jpg')
    >>> os.close(file_descriptor)
    >>> Image.new('RGB', (1,1)).save(file_path, 'JPEG')
    >>> metadata = pyexiv2.Image(file_path)
    >>> metadata.readMetadata()
    >>> keys = ('Exif.Photo.DateTimeOriginal',
    ...         'Iptc.Application2.DateCreated',
    ...         'Iptc.Application2.TimeCreated',)
    >>> # Note that metadata doesn't have microsecond precision.
    >>> exif_val = datetime.datetime(2007, 9, 28, 3, 0)
    >>> iptc_val = datetime.datetime(2007, 10, 10, 5, 0)
    >>> iptc_date = iptc_val.date()
    >>> iptc_time = iptc_val.time()
    
    >>> # Use this function
    >>> metadata['Exif.Photo.DateTimeOriginal'] = exif_val
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = iptc_date
    ... except TypeError:
    ...     pass
    >>> try:
    ...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys) == exif_val
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
    >>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys) == exif_val
    True
    
    >>> _del_img_key(metadata, 'Exif.Photo.DateTimeOriginal')
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = iptc_date
    ... except TypeError:
    ...     pass
    >>> try:
    ...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys) == iptc_val
    True
    
    >>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
    >>> _del_img_key(metadata, 'Iptc.Application2.TimeCreated')
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys)
    None
    
    >>> try:
    ...     metadata['Iptc.Application2.DateCreated'] = iptc_date
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys)
    None
    
    >>> _del_img_key(metadata, 'Iptc.Application2.DateCreated')
    >>> try:
    ...     metadata['Iptc.Application2.TimeCreated'] = iptc_time
    ... except TypeError:
    ...     pass
    >>> metadata.writeMetadata()
    >>> print read_datetime_from_exif_and_iptc(metadata, *keys)
    None
    
    >>> # Clean up.
    >>> os.remove(file_path)
    
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
