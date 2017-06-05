from flask_restful import reqparse, Resource
from http.client import OK, NOT_FOUND, NO_CONTENT, CREATED, BAD_REQUEST
import uuid
import json

from models import Order, OrderItem, Item, User, database


def is_valid_uuid(user_id):
    return uuid.UUID(user_id, version=4)


def is_valid_item_list(json_item_list):
    return json.loads(json_item_list)


class OrdersResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', type=is_valid_uuid, required=True)
        parser.add_argument('items', type=is_valid_item_list, required=True)
        args = parser.parse_args(strict=True)

        user_query = User.select().where(User.uuid == args['user'])
        if user_query.exists():
            user = user_query.get()
        else:
            return None, BAD_REQUEST

        total_price = 0

        items = args['items']
        items_uuid = [i[0] for i in items]
        items_query = Item.select().where(Item.uuid << items_uuid)

        if items_query.count() != len(items) or len(items) == 0:
            return None, BAD_REQUEST

        for item in items_query:
            item_quantity = [x[1] for x in items if x[0] == str(item.uuid)][0]
            total_price += float(item.price * item_quantity)

        with database.transaction():
            order = Order.create(
                uuid=uuid.uuid4(),
                total_price=total_price,
                user=user.id
            )

            for item in items_query:
                item_quantity = [x[1] for x in items if x[0] == str(item.uuid)][0]
                OrderItem.create(
                    order=order,
                    item=item.id,
                    quantity=item_quantity,
                    subtotal=float(item.price * item_quantity)
                )

        return order.json(), CREATED

    def get(self):
        return [order.json() for order in Order.select()], OK


class OrderResource(Resource):
    def get(self, uuid):
        try:
            return Order.get(Order.uuid == uuid).json(), OK
        except Order.DoesNotExist:
            return None, NOT_FOUND

    def put(self, uuid):
        order_query = Order.select().where(Order.uuid == uuid)
        if order_query.exists():
            order = order_query.get()
        else:
            return None, NOT_FOUND

        parser = reqparse.RequestParser()
        parser.add_argument('items', type=is_valid_item_list, required=True)
        args = parser.parse_args(strict=True)

        total_price = 0

        items = args['items']
        uuid = [i[0] for i in items]
        items_query = Item.select().where(Item.uuid << uuid)

        if items_query.count() != len(items) or len(items) == 0:
            return None, BAD_REQUEST

        for item in items_query:
            item_quantity = [x[1] for x in items if x[0] == str(item.uuid)][0]
            total_price += float(item.price * item_quantity)

        with database.transaction():
            OrderItem.delete().where(OrderItem.order == order).execute()

            for item in items_query:
                item_quantity = [x[1] for x in items if x[0] == str(item.uuid)][0]
                OrderItem.create(
                    order=order,
                    item=item.id,
                    quantity=item_quantity,
                    subtotal=float(item.price * item_quantity)
                )

            order.total_price = total_price
            order.save()

        return order.json(), OK

    def delete(self, uuid):
        order_query = Order.select().where(Order.uuid == uuid)
        if order_query.exists():
            order = order_query.get()
        else:
            return None, NOT_FOUND

        with database.transaction():
            order_items = OrderItem.select().where(
                OrderItem.order == order)

            for order_item in order_items:
                order_item.delete_instance()

            order.delete_instance()

        return None, NO_CONTENT
