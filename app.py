from flask import Flask, render_template, abort, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

pizza_topping = db.Table(
    "pizza_topping",
    db.Column(
        "pizza_id", db.Integer,
        db.ForeignKey("pizza.id"), # Points to Pizza Table
        primary_key = True
    ),
    db.Column(
        "topping_id", db.Integer,
        db.ForeignKey("topping.id"), # Points to Topping Table
        primary_key = True
    ),
)

class Pizza(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    price = db.Column(db.Float, nullable = False)
    
    toppings = db.relationship(
        "Topping",
        secondary = pizza_topping,
        backref = "pizzas"
    )
    
class Topping(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pizza.db"
    app.config["SQLALCHEMY_TRACK_URI"] = False
    app.config["SECRET_KEY"] = "something-goes-here"
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        if Pizza.query.count() == 0:    
            # Create Topping Object
            t_cheese = Topping(name = "Cheese")
            t_tomato = Topping(name = "Tomato Sauce")
            t_pepperoni = Topping(name = "Pepperoni")
            t_ham = Topping(name = "Ham")
            t_pineapple = Topping(name = "Pineapple")
            t_sausage = Topping(name = "Italian Fennel Sausage")
            t_basil = Topping(name = "Basil")
            
            db.session.add_all([t_cheese, t_tomato, t_pepperoni, t_ham, t_pineapple, t_sausage, t_basil])
            
            # Create Pizza Object
            p1 = Pizza(name = "Margherita", price = 11)
            p2 = Pizza(name = "Hawaiian", price = 12.50)
            p3 = Pizza(name = "Pepperoni", price = 11.50)
            p4 = Pizza(name = "Italian Sausage", price = 14)
            
            db.session.add_all([p1, p2, p3, p4])
            
            # Connect Pizza to Topping
            p1.toppings.extend([t_tomato, t_cheese, t_basil])
            p2.toppings.extend([t_tomato, t_cheese, t_ham, t_pineapple])
            p3.toppings.extend([t_tomato, t_cheese, t_pepperoni])
            p4.toppings.extend([t_tomato, t_cheese, t_sausage, t_basil])
            
            db.session.commit()

    @app.route("/")
    def home():
        return render_template(
            "home.html",
            page_title = "Home",
            greeting = "Hello, Daniel Peter James Kersten (the one born on May 5th 2009)! I've been expecting you... have you done your calculus homework?"
            )
        
    @app.route("/pizzas")
    def pizzas_page():
        pizzas = Pizza.query.order_by(Pizza.name.asc()).all()
        return render_template(
            "pizzas.html",
            page_title = "Pizzas",
            pizzas = pizzas
            )
        
    @app.route("/pizzas/<int:pizza_id>")
    def pizza_detail(pizza_id):
        pizza = Pizza.query.get(pizza_id)
        if pizza is None:
            abort(404)
        return render_template(
            "pizza_detail.html", 
            page_title="pizza.name", 
            pizza=pizza
            )   

    return app
        
app = create_app()

if __name__ == "__main__":
    app.run(debug = True, host = "127.0.0.1", port = 5000)
