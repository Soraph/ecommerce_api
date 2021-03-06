from http.client import NO_CONTENT
from http.client import NOT_FOUND
from http.client import OK
from .base_test import BaseTest
from models import Picture
import hashlib
import uuid
import os


class TestPicture(BaseTest):

    def test_get_picture(self):
        picture1 = self.create_item_picture()

        resp = self.open('/pictures/{}'.format(picture1.uuid), 'get', data='')

        m = hashlib.sha256()
        m.update(resp.data)
        hash_response = m.digest()

        with open(os.path.join('.', 'tests', 'images', 'test_image.png'), 'rb') as image:
            image = image.read()

            h4sh = hashlib.sha256()
            h4sh.update(image)
            hash_image = h4sh.digest()

        assert resp.status_code == OK
        assert hash_response == hash_image

    def test_get_picture_not_existing_picture(self):
        resp = self.open('/pictures/{}'.format(uuid.uuid4()), 'get', data='')
        assert resp.status_code == NOT_FOUND

    def test_delete_picture_succed(self):
        picture1 = self.create_item_picture()

        resp = self.open('/pictures/{}'.format(picture1.uuid), 'delete', data='')
        assert resp.status_code == NO_CONTENT
        assert len(Picture.select()) == 0
        resp = self.open('/pictures/{}'.format(picture1.uuid), 'get', data='')
        assert resp.status_code == NOT_FOUND

    def test_delete_picture_failure_not_found(self):
        resp = self.open('/picture/{}'.format(uuid.uuid4()), 'delete', data='')
        assert resp.status_code == NOT_FOUND
