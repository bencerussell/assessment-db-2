from flask import Flask, render_template, abort, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

manufacturer_operator = db.Table(
    "manufacturer_operator",
    db.Column(
        "operator_icao", db.String,
        db.ForeignKey("operator.icao"), 
        primary_key = True
    ),
    db.Column(
        "manufacturer_id", db.Integer,
        db.ForeignKey("manufacturer.id"),
        primary_key = True
    ),
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(254), nullable = False, unique = True)

class Operator(db.Model):
    icao = db.Column(db.String(3), primary_key = True)
    hub_icao = db.Column(db.String(4), nullable = False)
    year_founded = db.Column(db.Integer, nullable = False)
    operator_name = db.Column(db.String(25), nullable = False)
    
    manufacturers = db.relationship(
        "Manufacturer",
        secondary = manufacturer_operator,
        back_populates = "operators"
    )
    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "operator"
    )
    
class Manufacturer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    manufacturer_name = db.Column(db.String(15), nullable = False)

    operators = db.relationship(
        "Operator",
        secondary = manufacturer_operator,
        back_populates = "manufacturers"
    )

class Aircraft(db.Model):
    registration = db.Column(db.String(8), primary_key = True)
    country = db.Column(db.String(3), nullable = False)
    year_produced = db.Column(db.String(4), nullable = False)
    aircraft_icao = db.Column(db.String(5), nullable = False)
    operator_id = db.Column(db.String(3), db.ForeignKey("operator.icao"), nullable=False)

    operator = db.relationship(
        "Operator",
        back_populates = "aircrafts"
    )

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///plane.db"
    app.config["SQLALCHEMY_TRACK_MODIFICTIONS"] = False
    app.config["SECRET_KEY"] = "DanielPJKersten"
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username="admin").first():
            user = User(
                username="admin",
                email="bencerussell@garincollege.nz",
                password=generate_password_hash("password123")
            )
            db.session.add(user)
            db.session.commit()
            
       ## if Aircraft.query.count() == 0:    
       ##     # Create Topping Object
       ##     t_cheese = Topping(name = "Cheese")
       ##     t_tomato = Topping(name = "Tomato Sauce")
       ##     t_pepperoni = Topping(name = "Pepperoni")
       ##     t_ham = Topping(name = "Ham")
       ##     t_pineapple = Topping(name = "Pineapple")
       ##     t_sausage = Topping(name = "Italian Fennel Sausage")
       ##     t_basil = Topping(name = "Basil")
       ##     
       ##     db.session.add_all([t_cheese, t_tomato, t_pepperoni, t_ham, t_pineapple, t_sausage, t_basil])
       ##     
       ##     # Create Pizza Object
       ##     p1 = Pizza(name = "Margherita", price = 11)
       ##     p2 = Pizza(name = "Hawaiian", price = 12.50)
       ##     p3 = Pizza(name = "Pepperoni", price = 11.50)
       ##     p4 = Pizza(name = "Italian Sausage", price = 14)
       ##     
       ##     db.session.add_all([p1, p2, p3, p4])
       ##     
       ##     # Connect Pizza to Topping
       ##     p1.toppings.extend([t_tomato, t_cheese, t_basil])
       ##     p2.toppings.extend([t_tomato, t_cheese, t_ham, t_pineapple])
       ##     p3.toppings.extend([t_tomato, t_cheese, t_pepperoni])
       ##     p4.toppings.extend([t_tomato, t_cheese, t_sausage, t_basil])
       ##     
       ##     db.session.commit()

    @app.route("/")
    def home():
        return render_template(
            "home.html",
            page_title = "Home",
            greeting = "Hello, Daniel Peter James Kersten (the one born on May 5th 2009)! I've been expecting you... have you done your calculus homework?"
            )
        
    @app.route("/about-us")
    def about_us():
        return render_template(
            "about-us.html",
            page_title = "About Us",
            )
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        create_account = False

        if request.method == "POST":
            action = request.form["action"]

            if action == "create":
                create_account = True
            elif action == "actualcreate":
                create_account = True

                username = request.form["username"]
                password = request.form["password"]
                email = request.form["email"]
                confirmpassword = request.form["confirm_password"]

                if password != confirmpassword:
                    error = "Passwords do not match."
                elif User.query.filter_by(username=username).first():
                    error = "Username already exists."
                elif User.query.filter_by(email=email).first():
                    error = "Email already in use."
                else:
                    new_user = User(
                        username=username,
                        email=email,
                        password=generate_password_hash(password)
                    )

                    db.session.add(new_user)
                    db.session.commit()

                    session["user"] = username
                    
                    next_page = request.args.get("next")

                    if not next_page:
                        next_page = url_for("home")

                    return redirect(next_page)

            elif action == "login":
                username = request.form["username"]
                password = request.form["password"]

                user = User.query.filter_by(username=username).first()

                next_page = request.args.get("next")

                if user and check_password_hash(user.password, password):
                    session["user"] = username
                    if not next_page:
                        next_page = url_for("home")

                    return redirect(next_page)
                else:
                    error = "Invalid username or password."

        return render_template(
            "login.html",
            page_title = "Login",
            error=error,
            create_account=create_account
        )
    
    @app.route("/profile")
    def profile():
        if "user" in session:
            return render_template(
                "profile.html",
                page_title = "Profile",
                user = session["user"],
                email = user.email if (user := User.query.filter_by(username=session["user"]).first()) else None
            )
        else:
            return redirect(url_for("login"))
        
    @app.route("/database")
    def database():
        if "user" in session:
            return render_template(
                "database.html",
                page_title = "Database",
            )
        else:
            return redirect(url_for("login", next=request.url))

    @app.route("/dashboard")
    def dashboard():
        if "user" in session:
            return render_template(
                "dashboard.html",
                page_title = "Dashboard",
                user = session["user"]
            )
        else:
            return redirect(url_for("login", next=request.url))
    
    @app.route("/logout")
    def logout():
        session.pop("user", None)
        return redirect(url_for("home"))
        
   # @app.route("/pizzas/<int:pizza_id>")
   # def pizza_detail(pizza_id):
   #     pizza = Pizza.query.get(pizza_id)
   #     if pizza is None:
   #         abort(404)
   #     return render_template(
   #         "pizza_detail.html", 
   #         page_title="pizza.name", 
   #         pizza=pizza
   #         )   

    return app
        
app = create_app()

@app.context_processor
def inject_user():
   return{
       "logged_in": "user" in session   
   }

if __name__ == "__main__":
    app.run(debug = True, host = "127.0.0.1", port = 5000)
