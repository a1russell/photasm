from django.contrib.auth.models import User
from django.test import TestCase

from photasm.photos.models import Album


class AlbumNameWithOwnerTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user('adam', 'adam@example.com',
                                              'adampassword')
        self.album1 = Album.objects.create(owner=self.user1, name='Foo')
        self.user2 = User.objects.create_user('lewis', 'lewis@example.com',
                                              'lewispassword')
        self.album2 = Album.objects.create(owner=self.user2, name='Bar')
        self.user3 = User.objects.create_user('thien', 'thien@example.com',
                                              'thienpassword')
        self.user3.first_name = "Thien"
        self.user3.save()
        self.album3 = Album.objects.create(owner=self.user3, name='Baz')

    def tearDown(self):
        User.objects.all().delete()
        Album.objects.all().delete()

    def runTest(self):
        self.assertEqual(self.album1.name_with_owner, "adam's Foo")
        self.assertEqual(self.album2.name_with_owner, "lewis' Bar")
        self.assertEqual(self.album3.name_with_owner, "Thien's Baz")
