from cloudinary.api import delete_resources_by_tag, resources_by_tag
from models import Item, User, Address, Order, OrderItem, Picture
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from models import Item, User, Address, Order, OrderItem, Favorites, Picture
from peewee import SqliteDatabase

from views.user import crypt_password
from app import app
import base64
import uuid
from uuid import UUID
import os
import simplejson as json


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

        return obj.__dict__


class BaseTest:
    @classmethod
    def setup_class(cls):
        database = SqliteDatabase(':memory:')

        cls.tables = [Item, User, Address, Order, OrderItem, Favorites, Picture]
        for table in cls.tables:
            table._meta.database = database
            table.create_table()

        app.config['TESTING'] = True
        app.config['CLOUDINARY_DEFAULT_TAG'] = 'test_pictures'

        cls.DEFAULT_TAG = app.config['CLOUDINARY_DEFAULT_TAG']
        cls.app = app.test_client()

    @classmethod
    def teardown_class(cls):
        response = resources_by_tag(cls.DEFAULT_TAG)
        resources = response.get('resources', [])
        if resources:
            delete_resources_by_tag(cls.DEFAULT_TAG)

    def setup_method(self):
        for table in self.tables:
            table.delete().execute()

    def create_user(self, email="email@domain.com", first_name="First Name",
                    last_name="Last name", password="p4ssw0rd", superuser=False):
        return User.create(
            uuid=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=crypt_password(password),
            superuser=superuser,
        )

    def create_item(self, name="Item name", price=7,
                    description="Item description", category="Category", availability=11):
        return Item.create(
            uuid=uuid.uuid4(),
            name=name,
            price=price,
            description=description,
            category=category,
            availability=availability,
        )

    def create_order(self, user=None, items=None):
        '''Parameter format:

        items = [
            [Instance of Item, quantity],
            ...
            [instance of item, quantity]
        ]

        user = Instance of User
        '''
        if not user:
            user = self.create_user()

        if not items:
            items = []
            for i in range(2):
                item = self.create_item()
                items.append([item, i + 1])

        total_price = 0

        for item in items:
            total_price += float(item[0].price * item[1])

        order = Order.create(
            uuid=uuid.uuid4(),
            total_price=total_price,
            user=user
        )

        for item in items:
            item_quantity = item[1]
            item = item[0]

            OrderItem.create(
                order=order,
                item=item,
                quantity=item_quantity,
                subtotal=float(item.price * item_quantity)
            )

        return order

    def create_address(self, user=None, nation="Italy", city="Prato",
                       postal_code="59100", local_address="Via Roncioni 10",
                       phone="0574100100"):

        if not user:
            user = self.create_user()

        return Address.create(
            uuid=uuid.uuid4(),
            user=user,
            nation=nation,
            city=city,
            postal_code=postal_code,
            local_address=local_address,
            phone=phone,
        )

    def create_item_picture(self, item=None, title='Picture title', extension='jpeg'):
        if not item:
            item = self.create_item()

        picture = Picture.create(
            uuid=uuid.uuid4(),
            title=title,
            extension=extension,
            item=item
        )

        config = app.config

        with open(os.path.join('.', 'tests', 'images', 'test_image.png'), 'rb') as image:
            image = FileStorage(image)
            save_path = os.path.join('.', config['UPLOADS_FOLDER'], 'items', str(item.uuid))
            new_filename = secure_filename('.'.join([str(picture.uuid), picture.extension]))

            os.makedirs(save_path, exist_ok=True)

            image.save(os.path.join(save_path, new_filename))

        return picture

    def open(self, url, method, data, content_type='application/json'):
        if content_type == 'application/json':
            data = json.dumps(data, cls=UUIDEncoder)

        return self.app.open(
            url, method=method, data=data, content_type=content_type
        )

    def open_with_auth(self, url, method, email, password, data, content_type='application/json'):
        if content_type == 'application/json':
            data = json.dumps(data, cls=UUIDEncoder)

        headers = {'Authorization': 'Basic ' + base64.b64encode(
            bytes(email + ":" + password, 'ascii')).decode('ascii')}

        return self.app.open(
            url, method=method, headers=headers, data=data, content_type=content_type
        )
