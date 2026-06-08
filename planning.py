# THIS IS A PLANNING FILE - NOT CONNECTED TO THE APP

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

pizza_topping = db.Table(
    "pizza_topping",
    db.Column(
        "pizza_id", db.integer,
        db.ForeignKey("pizza.id"), # Points to Pizza Table
        primary_key = True
    ),
    db.Column(
        "topping_id", db.integer,
        db.ForeignKey("topping.id"), # Points to Topping Table
        primary_key = True
    ),
    
)

class Pizza(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    price = db.Column(db.Float, nullable = False)
    
class Topping(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    