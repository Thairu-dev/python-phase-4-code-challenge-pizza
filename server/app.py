#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)



@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# Route to get all restaurants
class Restaurants(Resource):
    def get(self):
        restaurants = [restaurant.to_dict() for restaurant in Restaurant.query.all()]
        for restaurant in restaurants:
            restaurant.pop('restaurant_pizzas', None)
        return make_response(jsonify(restaurants), 200)

api.add_resource(Restaurants, "/restaurants")

# Get restaurantById
class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant is None:
            return {"error": "Restaurant not found"}, 404
        response_dict = restaurant.to_dict()
        response_dict['restaurant_pizzas'] = [rp.to_dict() for rp in restaurant.restaurant_pizzas]
        return response_dict, 200
    
    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant is None:
            return {"error": "Restaurant not found"}, 404

        # Delete associated RestaurantPizzas if not set to cascade delete
        for rp in restaurant.restaurant_pizzas:
            db.session.delete(rp)

        db.session.delete(restaurant)
        db.session.commit()
        return {}, 204

api.add_resource(RestaurantByID, "/restaurants/<int:id>")

class Pizzas(Resource):
    def get(self):
        pizzas = [pizza.to_dict() for pizza in Pizza.query.all()]
        return make_response(jsonify(pizzas), 200)

api.add_resource(Pizzas, "/pizzas")


@app.route('/restaurant_pizzas', methods=['POST'])
def add_restaurant_pizza():
    data = request.get_json()
    
    # Validate input data
    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    if not (price and pizza_id and restaurant_id):
        return make_response( {"errors": ["validation errors"]}, 400)

    try:
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        restaurant = Restaurant.query.filter(Restaurant.id==restaurant_id).first()
        pizza = Pizza.query.filter(Pizza.id==pizza_id).first()
        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }
        return make_response(response_data, 201)
    except ValueError as e:
        return make_response( {"errors": ["validation errors"]}, 400)


if __name__ == "__main__":
    app.run(port=5555, debug=True)
