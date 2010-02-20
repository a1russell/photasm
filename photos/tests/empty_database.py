from django.core.urlresolvers import reverse
from django.test import TestCase


class EmptyDataBaseTest(TestCase):

    def test_photo_detail(self):
        photo_view = 'photasm.photos.views.photo_detail'

        photo_url = reverse(photo_view, args=[0])
        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, 404)
