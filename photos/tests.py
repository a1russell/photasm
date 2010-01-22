"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from photasm.photos.image_metadata import (
    _collapse_empty_to_none,
    _del_img_key,
    _is_iter,
    _metadata_value_synced_with_file,
    _sync_metadata_value_to_file,
    datetime_synced_with_exif_and_iptc,
    get_image_height_key,
    get_image_width_key,
    read_datetime_from_exif_and_iptc,
    read_value_from_exif_and_iptc,
    require_pyexiv2_obj,
    sync_datetime_to_exif_and_iptc,
    sync_value_to_exif,
    sync_value_to_exif_and_iptc,
    sync_value_to_iptc,
    value_synced_with_exif,
    value_synced_with_exif_and_iptc,
    value_synced_with_iptc,
)


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)


__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


image_metadata_tests = {
    '_collapse_empty_to_none': _collapse_empty_to_none,
    '_del_img_key': _del_img_key,
    '_is_iter': _is_iter,
    '_metadata_value_synced_with_file': _metadata_value_synced_with_file,
    '_sync_metadata_value_to_file': _sync_metadata_value_to_file,
    'datetime_synced_with_exif_and_iptc': datetime_synced_with_exif_and_iptc,
    'get_image_height_key': get_image_height_key,
    'get_image_width_key': get_image_width_key,
    'read_datetime_from_exif_and_iptc': read_datetime_from_exif_and_iptc,
    'read_value_from_exif_and_iptc': read_value_from_exif_and_iptc,
    'require_pyexiv2_obj': require_pyexiv2_obj,
    'sync_datetime_to_exif_and_iptc': sync_datetime_to_exif_and_iptc,
    'sync_value_to_exif': sync_value_to_exif,
    'sync_value_to_exif_and_iptc': sync_value_to_exif_and_iptc,
    'sync_value_to_iptc': sync_value_to_iptc,
    'value_synced_with_exif': value_synced_with_exif,
    'value_synced_with_exif_and_iptc': value_synced_with_exif_and_iptc,
    'value_synced_with_iptc': value_synced_with_iptc,
}
__test__.update(image_metadata_tests)
