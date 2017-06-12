import json
from werkzeug.datastructures import FileStorage
from cloudinary.api import resources_by_tag
from http.client import CREATED
from http.client import NO_CONTENT
from http.client import NOT_FOUND
from http.client import OK
from http.client import BAD_REQUEST
from http.client import UNAUTHORIZED
from models import Item
import uuid
import os

from .base_test import BaseTest


class TestItems(BaseTest):
    def test_get_items__empty(self):
        resp = self.open('/items/', 'get', data='')
        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == []

    def test_get_items(self):
        item1 = self.create_item()
        item2 = self.create_item()

        resp = self.open('/items/', 'get', data='')
        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == [item1.json(), item2.json()]

    def test_create_item__failure_user_is_not_superuser(self):
        user = self.create_user()
        new_item_data = {
            'name': 'Product',
            'price': 123,
            'description': 'Info',
            'category': 'Domestici',
            'availability': 5
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == UNAUTHORIZED

    def test_create_item__success(self):
        user = self.create_user(superuser=True)

        new_item_data = {
            'name': 'Item one',
            'price': 15,
            'description': 'desc1',
            'category': 'poligoni',
            'availability': 11
        }

        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == CREATED

        item_from_server = json.loads(resp.data.decode())
        item_from_db = Item.get(Item.uuid == item_from_server['uuid']).json()

        assert len(Item.select()) == 1
        assert item_from_db == item_from_server

        item_from_server.pop('uuid')
        assert item_from_server == new_item_data

    def test_create_item__failure_invalid_field_value(self):
        user = self.create_user(superuser=True)
        new_item_data = {
            'name': 'Item one',
            'price': 15,
            'description': 'desc1',
            'category': 'poligoni',
            'availability': -8
        }

        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)

        assert resp.status_code == BAD_REQUEST

    def test_create_item__failure_empty_field(self):
        user = self.create_user(superuser=True)

        new_item_data = {
            'name': '',
            'price': 10,
            'description': 'Description one',
            'category': 'Category one',
            'availability': 11
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_create_item__failure_empty_field_only_spaces(self):
        user = self.create_user(superuser=True)

        new_item_data = {
            'name': '    ',
            'price': 5,
            'description': 'desc1',
            'category': 'varie',
            'availability': 11
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert Item.count() == 0

    def test_create_item__failure_missing_field(self):
        user = self.create_user(superuser=True)

        new_item_data = {
            'name': 'Item one',
            'description': 'Description one'
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert len(Item.select()) == 0

    def test_create_item__failure_field_wrong_type(self):
        user = self.create_user(superuser=True)

        new_item_data = {
            'name': 'Item one',
            'price': 'Ten',
            'description': 'Description one',
            'category': 'Category one'
        }
        resp = self.open_with_auth(
            '/items/', 'post', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST
        assert Item.count() == 0

    def test_get__item(self):
        item1 = self.create_item()

        resp = self.open('/items/{}'.format(item1.uuid), 'get', data='')
        assert resp.status_code == OK

        item_from_server = json.loads(resp.data.decode())
        assert item_from_server == item1.json()

    def test_get_item__empty(self):
        resp = self.open('/items/{}'.format(uuid.uuid4()), 'get', data='')
        assert resp.status_code == NOT_FOUND

    def test_get_item__failure_non_existing_item(self):
        self.create_item()

        resp = self.open('/items/{}'.format(uuid.uuid4()), 'get', data='')
        assert resp.status_code == NOT_FOUND

    def test_delete_item__failure_user_is_not_superuser(self):
        user = self.create_user()
        new_item = self.create_item()
        resp = self.open_with_auth(
            '/items/{}'.format(new_item.uuid), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == UNAUTHORIZED
        assert len(Item.select()) == 1

    def test_delete_item__success(self):
        user = self.create_user(superuser=True)
        item1 = self.create_item()

        resp = self.open_with_auth(
            'items/{}'.format(item1.uuid), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NO_CONTENT
        assert Item.count() == 0
        resp = self.open('item/{}'.format(item1.uuid), 'get', data='')
        assert resp.status_code == NOT_FOUND

    def test_delete_item__failure_not_found(self):
        user = self.create_user(superuser=True)
        self.create_item()

        resp = self.open_with_auth(
            'items/{}'.format(uuid.uuid4()), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NOT_FOUND
        assert len(Item.select()) == 1

    def test_delete_item__failure_non_existing_empty_items(self):
        user = self.create_user(superuser=True)

        resp = self.open_with_auth(
            'items/{}'.format(uuid.uuid4()), 'delete', user.email, 'p4ssw0rd', data='')
        assert resp.status_code == NOT_FOUND

    def test_modify_item__failure_user_is_not_superuser(self):
        user = self.create_user()
        item = self.create_item()

        new_data = {
            'name': 'item',
            'price': 10,
            'description': 'info product',
            'category': 'product category',
            'avaibility': 1
        }

        resp = self.open_with_auth(
            '/items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=new_data)
        assert resp.status_code == UNAUTHORIZED

        item_from_db = Item.get(uuid=item.uuid).json()
        assert item.json() == item_from_db

    def test_modify_item__success(self):
        user = self.create_user(superuser=True)
        item = self.create_item()
        new_item_data = {
            'name': 'Item one',
            'price': 10,
            'description': 'Descrizione sensata',
            'category': 'Poligoni',
            'availability': 0
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == OK

        item_from_server = json.loads(resp.data.decode())
        item_from_db = Item.get(Item.uuid == item_from_server['uuid']).json()

        assert item_from_db == item_from_server

        item_from_server.pop('uuid')
        assert new_item_data == item_from_server

    def test_modify_item__failure_invalid_field_value(self):
        user = self.create_user(superuser=True)
        item = self.create_item()
        new_item_data = {
            'name': 'Item one',
            'price': 10,
            'description': 'Descrizione sensata',
            'category': 'Poligoni',
            'availability': -8
        }

        resp = self.open_with_auth(
            '/items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_empty_field_only_spaces(self):
        user = self.create_user(superuser=True)
        item = self.create_item()
        modified_content = {
            'name': '      ',
            'price': 10,
            'description': 'Description two',
            'category': 'Category two',
            'availability': 11
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        item_from_db = item.reload().json()
        assert item.json() == item_from_db
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_missing_argument(self):
        user = self.create_user(superuser=True)
        item = self.create_item()
        modified_content = {
            'name': 'Item two',
            'price': 10,
            'description': 'Description two'
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        item_from_db = item.reload().json()
        assert item.json() == item_from_db
        assert resp.status_code == BAD_REQUEST

    def test_modify_item__failure_field_wrong_type(self):
        user = self.create_user(superuser=True)
        item = self.create_item()
        modified_content = {
            'name': 'Item one',
            'price': 'Ten',
            'description': 'Description two',
            'category': 'Category two',
            'availability': 6
        }
        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'put', user.email, 'p4ssw0rd', data=modified_content)
        assert resp.status_code == BAD_REQUEST

        item_from_db = item.reload().json()
        assert item.json() == item_from_db

    def test_modify_item_patch__success(self):
        user = self.create_user()
        item = self.create_item()

        new_item_data = {
            'name': 'Item one',
            'price': 10,
        }

        expected_new_data = {
            'name': 'Item one',
            'price': 10,
            'description': item.description,
            'category': item.category,
            'availability': item.availability,
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'patch', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == OK

        item_from_server = json.loads(resp.data.decode())
        item_from_db = Item.get(Item.uuid == item_from_server['uuid']).json()

        assert item_from_db == item_from_server

        item_from_server.pop('uuid')
        assert expected_new_data == item_from_server

    def test_modify_item_patch__failure_invalid_field_value(self):
        user = self.create_user()
        item = self.create_item()

        new_item_data = {
            'name': 'Item one',
            'price': 10,
            'availability': -8
        }

        resp = self.open_with_auth(
            '/items/{}'.format(item.uuid), 'patch', user.email, 'p4ssw0rd', data=new_item_data)
        assert resp.status_code == BAD_REQUEST

    def test_modify_item_patch__failure_empty_field_only_spaces(self):
        user = self.create_user()
        item = self.create_item()

        modified_content = {
            'name': '      ',
            'price': 10,
            'availability': 11
        }

        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'patch', user.email, 'p4ssw0rd', data=modified_content)
        item_from_db = item.reload().json()
        assert item.json() == item_from_db
        assert resp.status_code == BAD_REQUEST

    def test_modify_item_patch__failure_field_wrong_type(self):
        user = self.create_user()
        item = self.create_item()

        modified_content = {
            'name': 'Item one',
            'price': 'Ten',
            'availability': 6
        }
        resp = self.open_with_auth(
            'items/{}'.format(item.uuid), 'patch', user.email, 'p4ssw0rd', data=modified_content)
        assert resp.status_code == BAD_REQUEST

        item_from_db = item.reload().json()
        assert item.json() == item_from_db

    def test_reload(self):
        item = self.create_item(availability=5)
        assert item.availability == 5

        item.availability = 1
        assert item.availability == 1

        item.update(availability=0).where(Item.uuid == item.uuid).execute()
        assert item.availability == 1

        item = item.reload()
        assert item.availability == 0

        item_old = Item.get(Item.uuid == item.uuid)

        item.availability = 1
        item.save()

        assert item_old.availability == 0
        assert item_old.reload().availability == 1

    def test_create_item_picture__failure_user_is_not_superuser(self):
        user = self.create_user()
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')
        item = self.create_item()
        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.open_with_auth(
            '/items/{}/pictures'.format(item.uuid), 'post', user.email, 'p4ssw0rd',
            data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == UNAUTHORIZED

    def test_create_item_pictures__success(self):
        user = self.create_user(superuser=True)
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }
        resp = self.open_with_auth(
            '/items/{}/pictures'.format(item.uuid), 'post', user.email, 'p4ssw0rd',
            data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == CREATED

        image_from_server = json.loads(resp.data.decode())
        assert image_from_server['title'] == picture_data['title']
        assert image_from_server['extension'] == 'jpg'

        response = resources_by_tag(self.DEFAULT_TAG)
        resources = response.get('resources', [])
        assert len(resources) == 1

        assert resources[0]['public_id'] == image_from_server['uuid']

    def test_create_item_pictures__failure_empty_title_only_spaces(self):
        user = self.create_user(superuser=True)
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        item = self.create_item()

        picture_data = {
            'title': '  ',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.open_with_auth(
            '/items/{}/pictures'.format(item.uuid), 'post', user.email,
            'p4ssw0rd', data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == BAD_REQUEST

    def test_create_item_pictures__failure_missing_image(self):
        user = self.create_user(superuser=True)
        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': None,
        }

        resp = self.open_with_auth(
            '/items/{}/pictures'.format(item.uuid), 'post', user.email, 'p4ssw0rd',
            data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == BAD_REQUEST

    def test_create_item_pictures__failure_non_existing_item(self):
        user = self.create_user(superuser=True)
        test_image_path = os.path.join('.', 'tests', 'images', 'test_image.jpg')

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.open_with_auth(
            '/items/{}/pictures'.format(uuid.uuid4), 'post', user.email, 'p4ssw0rd',
            data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == NOT_FOUND

    def test_create_item_pictures__failure_not_an_image(self):
        user = self.create_user(superuser=True)
        test_image_path = os.path.join('.', 'tests', 'images', 'not_an_image.log')

        item = self.create_item()

        picture_data = {
            'title': 'Example image',
            'file': FileStorage(open(test_image_path, 'rb')),
        }

        resp = self.open_with_auth(
            '/items/{}/pictures'.format(item.uuid), 'post', user.email, 'p4ssw0rd',
            data=picture_data, content_type='multipart/form-data')
        assert resp.status_code == BAD_REQUEST

    def test_get_item_pictures__success(self):
        item = self.create_item()

        image1 = self.create_item_picture(item)
        image2 = self.create_item_picture(item)

        resp = self.open('/items/{}/pictures'.format(item.uuid), 'get', data='')

        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == [image1.json(), image2.json()]

    def test_get_item_pictures__success_empty_pictures(self):
        item = self.create_item()

        resp = self.open('/items/{}/pictures'.format(item.uuid), 'get', data='')

        assert resp.status_code == OK
        assert json.loads(resp.data.decode()) == []

    def test_get_item_pictures__failure_non_existing_item(self):
        resp = self.open('/items/{}/pictures'.format(uuid.uuid4()), 'get', data='')

        assert resp.status_code == NOT_FOUND
