import simplejson as json
from flask import Flask, make_response
from flask_restful import Api

from models import database

from views.item import ItemResource, ItemsResource, ItemPicturesResource
from views.order import OrderResource, OrdersResource
from views.user import UserResource, UsersResource
from views.address import AddressResource, AddressesResource
from views.favorites import FavoritesResource, FavoriteResource
from views.picture import PictureResource


app = Flask(__name__)
api = Api(app)
app.config['UPLOADS_FOLDER'] = 'images'
app.config['ALLOWED_EXTENSIONS'] = set(['jpg', 'jpeg', 'png'])
app.config['CLOUDINARY_DEFAULT_TAG'] = 'item_picture'


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


@app.before_request
def database_connect():
    if database.is_closed():
        database.connect()


@app.teardown_request
def database_disconnect(response):
    if not database.is_closed():
        database.close()
    return response


api.add_resource(ItemsResource, '/items/')
api.add_resource(ItemResource, '/items/<uuid:uuid>')
api.add_resource(ItemPicturesResource, '/items/<uuid:item_id>/pictures')
api.add_resource(UsersResource, '/users/')
api.add_resource(UserResource, '/users/<uuid:uuid>')
api.add_resource(OrdersResource, '/orders/')
api.add_resource(OrderResource, '/orders/<uuid:uuid>')
api.add_resource(AddressesResource, '/addresses/')
api.add_resource(AddressResource, '/addresses/<uuid:address_id>')
api.add_resource(FavoritesResource, '/favorites/')
api.add_resource(FavoriteResource, '/favorites/<uuid:item_id>')
api.add_resource(PictureResource, '/pictures/<uuid:uuid>')
