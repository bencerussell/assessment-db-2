from flask import Flask, render_template, abort, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import csv, requests, random

APIURL = "http://127.0.0.1:8787"

db = SQLAlchemy()

manufacturer_operator = db.Table( # many-many relationship table - currently no use but for references
    "manufacturer_operator",
    db.Column(
        "operator_icao", db.String,
        db.ForeignKey("operator.icao"), 
        primary_key = True
    ),
    db.Column(
        "manufacturer_id", db.Integer,
        db.ForeignKey("manufacturer.type_icao"),
        primary_key = True
    ),
)

# --ALL TABLES RELATING TO THE DATABASE--

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(254), nullable = False, unique = True)
    admin = db.Column(db.Boolean, default = False)

    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "user"
    )
    operators = db.relationship(
        "Operator",
        back_populates = "user"
    )

class Operator(db.Model):
    icao = db.Column(db.String(3), primary_key = True)
    hub_icao = db.Column(db.String(4), nullable = False)
    year_founded = db.Column(db.Integer, nullable = False)
    operator_name = db.Column(db.String(25), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = True)
    date_time = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)
    callsign = db.Column(db.String(50))
    
    manufacturers = db.relationship(
        "Manufacturer",
        secondary = manufacturer_operator,
        back_populates = "operators"
    )
    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "operator"
    )
    user = db.relationship(
        "User",
        back_populates = "operators"
    )
    
class Manufacturer(db.Model):
    manufacturer_id = db.Column(db.Integer, primary_key = True)
    type_icao = db.Column(db.String(4), nullable = False)
    manufacturer_name = db.Column(db.String(50), nullable = False)
    model_name = db.Column(db.String(50), nullable = False)
    wake_cat = db.Column(db.String(1), nullable = False)

    operators = db.relationship(
        "Operator",
        secondary = manufacturer_operator,
        back_populates = "manufacturers"
    )

    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "manufacturer"
    )

class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    registration = db.Column(db.String(10), nullable = False)
    year_produced = db.Column(db.Integer, nullable = True)
    operator_id = db.Column(db.String(3), db.ForeignKey("operator.icao"), nullable=False)
    registration_prefix = db.Column(db.String(5), db.ForeignKey("registration_prefix.prefix"), nullable=False)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey("manufacturer.manufacturer_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = True)
    date_time = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    __table_args__ = ( # Checks that the combination of the prefix and registration are unique, so something like ZK-ABC can exist, but so can VH-ABC and not a second ZK-ABC.
        db.UniqueConstraint(
            "registration_prefix",
            "registration",
            name = "unique_registration"
        ),
    )

    operator = db.relationship(
        "Operator",
        back_populates = "aircrafts"
    )

    prefix = db.relationship(
        "RegistrationPrefix",
        back_populates = "aircrafts"
    )

    manufacturer = db.relationship(
        "Manufacturer",
        back_populates = "aircrafts"
    )

    user = db.relationship(
        "User",
        back_populates = "aircrafts"
    )

class RegistrationPrefix(db.Model):
    __tablename__ = "registration_prefix"

    prefix = db.Column(db.String(10), primary_key = True)
    country_name = db.Column(db.String(50), nullable = False)
    country_id = db.Column(db.String(3), nullable = False)

    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "prefix"
    )

# --DATABASE TABLES END--

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///plane.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "DanielPJKersten"
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

        if Manufacturer.query.count() == 0: # Inputs manufacturers from a csv file when needed to repopulate the database
            with open('ac_type.csv', newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    manufacturer = Manufacturer(
                        manufacturer_name = row["manufacturer_name"],
                        model_name = row["model_name"],
                        type_icao = row["type_icao"],
                        wake_cat = row["wake_cat"]
                    )
                    db.session.add(manufacturer)

            db.session.commit()

        if RegistrationPrefix.query.count() == 0: # Inputs registration prefixes from a csv file when needed to repopulate the database
            with open('registration_prefixes.csv', newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    prefix = RegistrationPrefix(
                        prefix = row["prefix"],
                        country_name = row["country_name"],
                        country_id = row["country_id"]
                    )
                    db.session.add(prefix)

            db.session.commit()

        if Aircraft.query.count() == 0: # Inputs manufacturers from a csv file when needed to repopulate the database
            with open('aircraft.csv', newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    aircraft = Aircraft(
                        registration = row["registration"],
                        year_produced = row["year"],
                        operator_id = row["operator"],
                        registration_prefix = row["prefix"],
                        manufacturer_id = row["manufacturer"],
                        user_id = 1
                    )
                    db.session.add(aircraft)

        db.session.commit()

            

        if not User.query.filter_by(username="admin").first(): # Creates admin account if hasn't already been done
            user = User(
                username="admin",
                email="bencerussell@garincollege.nz",
                password=generate_password_hash("password123"),
                admin=True
            )
            db.session.add(user)
            db.session.commit()

        if Operator.query.count() == 0: # Creates a base set of operators, especially that for privately owned aircraft if none already exist
            op1 = Operator(icao="ANZ", hub_icao="NZAA", year_founded=1940, operator_name="Air New Zealand", user_id=1, callsign="New Zealand")
            op2 = Operator(icao="VOZ", hub_icao="YBBN", year_founded=2000, operator_name="Virgin Australia", user_id=1, callsign="Velocity")
            op3 = Operator(icao="QFA", hub_icao="YSSY", year_founded=1920, operator_name="Qantas", user_id=1, callsign="Qantas")
            op4 = Operator(icao="BAW", hub_icao="EGLL", year_founded=1924, operator_name="British Airways", user_id=1, callsign="Speedbird")
            op5 = Operator(icao="NIL", hub_icao="NONE", year_founded=0, operator_name="Privately Owned", user_id=1)

            db.session.add_all([op5, op1, op2, op3, op4]) # Adds the 5 previously defined operators
            db.session.commit()

    @app.route("/")
    def home():
        return render_template(
            "home.html",
            page_title = "Home",
            greeting = "Welcome to AeroBase"
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

            if action == "create": # action == "create" when someone selects that they want to create an account, rather than redirecting them to a new page. This reloads the page to show the create_account options on the page.
                create_account = True 
            elif action == "actualcreate": # action == "actualcreate" when someone actually clicks 'create account' after inputting their information.
                create_account = True

                username = request.form["username"]
                password = request.form["password"]
                email = request.form["email"]
                confirmpassword = request.form["confirm_password"]

                if password != confirmpassword: # checks if passwords match
                    error = "Passwords do not match."
                elif User.query.filter_by(username=username).first(): # checks if username already exists
                    error = "Username already exists."
                elif User.query.filter_by(email=email).first(): # checks if email is already in use
                    error = "Email already in use."
                elif ' ' in username or ' ' in email: # checks if there are any spaces in the username or email
                    error = "Username/email cannot have spaces."
                elif len(username) > 20: # checks if username is too long
                    error = "Username cannot be longer than 20 characters."
                elif len(password) < 8 or len(password) > 100: # checks if password is too short or too long
                    error = "Password must be between 8 and 100 characters."
                else:
                    new_user = User(
                        username=username,
                        email=email,
                        password=generate_password_hash(password) # uses werkzeug to convert a string to a secure encrypted hash
                    )

                    db.session.add(new_user)
                    db.session.commit()

                    session["user"] = username
                    
                    next_page = request.args.get("next") # If users have been redirected to login from an original page, it will redirect them to the original page

                    if not next_page:
                        next_page = url_for("home") # If the above is not met, users will be redirected to the home page

                    return redirect(next_page) # Does the actual redirecting

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
            user = User.query.filter_by(username=session["user"]).first()

            return render_template(
                "profile.html",
                page_title="Profile",
                email=user.email,
                user=user.username
            )
        else:
            return redirect(url_for("login"))

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

    @app.route("/db-add", methods=["GET", "POST"])
    def db_add():
        type = None
        operators = Operator.query.order_by(Operator.operator_name).all() # Pulls a list of all operators to use in a <select> HTML function
        prefixes = RegistrationPrefix.query.order_by(RegistrationPrefix.prefix).all() # Pulls a list of all registration prefixes to use in a <select> HTML function 
        manufacturers = Manufacturer.query.order_by(Manufacturer.manufacturer_name).all() # Pulls a list of all manufcaturers (in reality aircraft type ICAOs) to use in a <select> HTML function
        if "user" in session:
            if request.method == "POST":
                action = request.form["action"]

                if action == "aircraft":
                    type="aircraft"
                elif action == "operator":
                    type="operator"
                elif action == "manufacturer":
                    type="manufacturer"
                elif action == "submit_aircraft":
                    year_produced = request.form["year_produced"]
                    if year_produced:
                        try:
                            year_produced = int(request.form["year_produced"])
                        except ValueError:
                            year_produced = None

                    registration = request.form["registration"].upper()
                    prefix = request.form["prefix"]
                    aircraft_icao = request.form["icao"].upper()
                    operator_id = request.form["operator_id"]
                    user_id = User.query.filter_by(username=session["user"]).first().id
                    
                    if Aircraft.query.filter_by(registration=registration, registration_prefix=prefix).first():
                        error = "Aircraft with this registration already exists."
                        return render_template(
                            "db-add.html",
                            page_title = "Add to the Database",
                            type=type,
                            operators=operators,
                            prefixes=prefixes,
                            error=error
                        )

                    else:
                        new_aircraft = Aircraft(
                            registration=registration,
                            registration_prefix=prefix,
                            year_produced=year_produced,
                            manufacturer_id=aircraft_icao,
                            operator_id=operator_id,
                            user_id=user_id
                        )

                    db.session.add(new_aircraft)
                    db.session.commit()

                    return redirect(url_for("dashboard"))
                elif action == "submit_operator":
                    try:
                        year_founded = int(request.form["year"])
                    except ValueError:
                        return redirect(url_for("db_add")) #make this return to the relevant page 
                    icao = request.form["icao"].upper()
                    hub_icao = request.form["hub"].upper()
                    operator_name = request.form["name"].title()
                    user_id = User.query.filter_by(username=session["user"]).first().id
                    callsign=request.form["callsign"].title()

                    if Operator.query.filter_by(icao=icao).first():
                        error = "Operator with this ICAO code already exists."

                    else:
                        new_operator = Operator(
                            icao=icao,
                            hub_icao=hub_icao,
                            year_founded=year_founded,
                            operator_name=operator_name,
                            user_id=user_id,
                            callsign=callsign
                        )
                        db.session.add(new_operator)
                        db.session.commit()
                        return redirect(url_for("dashboard"))
            
            return render_template(
                "db-add.html",
                page_title = "Add to the Database",
                type=type,
                operators=operators,
                prefixes=prefixes,
                manufacturers=manufacturers
            )
        else:
            return redirect(url_for("login", next=request.url))

    @app.route("/database")
    def databass():
        if "user" in session:
            return render_template(
                "database.html",
                page_title = "Database",
                user=session["user"]
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/aircraft")
    def dbaircraft():
        aircraft = Aircraft.query.order_by(Aircraft.operator_id, Aircraft.registration_prefix, Aircraft.registration).all() # Pulls all aircraft from the database
        if "user" in session:
            return render_template(
                "aircraft.html",
                page_title = "Database (Aircraft)",
                user=session["user"],
                aircrafts=aircraft
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/aircraft/<aircraft_id>") # Redirects to the selected aircraft ID (from the database page)
    def aircraftdetail(aircraft_id):
        aircraft = Aircraft.query.get(aircraft_id) # Locates the aircraft in the database from the ID
        if aircraft is None:
            abort(404) # Aborts if it cannot find the aircraft in order to prevent further errors appearing
        prefix = aircraft.registration_prefix
        if prefix != "N" and prefix != "JA" and prefix != "HL" and prefix != "VP-A" and prefix!= "VP-B" and prefix != "VQ-B":
            registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
        else:  
            registration = f"{aircraft.registration_prefix}{aircraft.registration}"
        response = requests.get(
            APIURL,
            params={"registration":registration}
        )

        data = response.json() if response.status_code == 200 else None

        if "user" in session:
            return render_template(
                "aircraftdetail.html",
                page_title = f"Database ({aircraft.registration_prefix}-{aircraft.registration})", # Displays the page title using an f-string to include variables
                user=session["user"],
                aircraft=aircraft,
                photos=data["photos"] if data else None
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/aircraft/<aircraft_id>/delete")
    def deleteaircraft(aircraft_id):
        if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True:
            abort(403)
        aircraft=Aircraft.query.get(aircraft_id)
        if aircraft is None:
            abort(404)
        db.session.delete(aircraft)
        db.session.commit()
        return redirect(url_for("dbaircraft"))

    @app.route("/database/aircraft/<aircraft_id>/edit", methods=["GET", "POST"])
    def editaircraft(aircraft_id):
        if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True:
            abort(403)
        aircraft=Aircraft.query.get(aircraft_id)
        operators = Operator.query.order_by(Operator.operator_name).all() # Pulls a list of all operators to use in a <select> HTML function
        prefixes = RegistrationPrefix.query.order_by(RegistrationPrefix.prefix).all() # Pulls a list of all registration prefixes to use in a <select> HTML function 
        manufacturers = Manufacturer.query.order_by(Manufacturer.type_icao).all() # Pulls a list of all manufcaturers (in reality aircraft type ICAOs) to use in a <select> HTML function

        if aircraft is None:
            abort(404)

        prefix = aircraft.registration_prefix
        if prefix != "N" and prefix != "JA" and prefix != "HL" and prefix != "VP-A" and prefix!= "VP-B" and prefix != "VQ-B":
            registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
        else:  
            registration = f"{aircraft.registration_prefix}{aircraft.registration}"

        response = requests.get(
            APIURL,
            params={"registration": registration}
        )

        data = response.json() if response.status_code == 200 else None

        if request.method == "POST":
            action = request.form["action"]

            if action == "saveedit":
                year_produced = request.form["year_produced"]
                if year_produced:
                    try:
                        year_produced = int(request.form["year_produced"])
                    except ValueError:
                        year_produced = None
                aircraft_icao = request.form["icao"].upper()
                operator_id = request.form["operator_id"]

                aircraft.manufacturer_id = aircraft_icao
                aircraft.operator_id = operator_id
                aircraft.year_produced = year_produced
                db.session.commit()

                return redirect(url_for("aircraftdetail", aircraft_id=aircraft_id))

        return render_template(
            "aircraftedit.html",
            page_title=f"Edit ({aircraft.registration_prefix}-{aircraft.registration})",
            aircraft=aircraft,
            operators=operators,
            manufacturers=manufacturers,
            photos=data["photos"] if data else None
        )


    @app.route("/database/operators")
    def dboperator():
        operators = Operator.query.order_by(Operator.operator_name).all()
        if "user" in session:
            return render_template(
                "operators.html",
                page_title = "Database (Operators)",
                user=session["user"],
                operators=operators
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/operators/<operator_id>")
    def operatordetail(operator_id):
        operator=Operator.query.get(operator_id)
        data = None
        if operator is None:
            abort(404)

        if not operator.aircrafts:
            photo = None
        else:
            aircraft = random.choice(operator.aircrafts)
            prefix = aircraft.registration_prefix
            if prefix != "N" and prefix != "JA" and prefix != "HL" and prefix != "VP-A" and prefix!= "VP-B" and prefix != "VQ-B":
                    registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
            else:  
                registration = f"{aircraft.registration_prefix}{aircraft.registration}"
            response = requests.get(
                APIURL,
                params={"registration": registration}
            )

            data = response.json() if response.status_code == 200 else None

        if data != None:
            photos=data["photos"]
        else:
            photos=None

        return render_template(
            "operatordetail.html",
            page_title = f"Database ({operator.icao})",
            operator=operator,
            photos=photos,
            user=session["user"],
            registration=f"{aircraft.registration_prefix}-{aircraft.registration}" if operator.aircrafts else None,
            number = len(operator.aircrafts)
        )

    @app.route("/database/operator/<operator_id>/edit", methods=["GET", "POST"])
    def editoperator(operator_id):
        if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True:
            abort(403)
        if operator_id == "NIL":
            abort(403)
        operator=Operator.query.get(operator_id)
        data = None
        if operator is None:
            abort(404)

        if not operator.aircrafts:
            photo = None
        else:
            aircraft = random.choice(operator.aircrafts)
            prefix = aircraft.registration_prefix
            if prefix != "N" and prefix != "JA" and prefix != "HL" and prefix != "VP-A" and prefix!= "VP-B" and prefix != "VQ-B":
                    registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
            else:  
                registration = f"{aircraft.registration_prefix}{aircraft.registration}"
            response = requests.get(
                APIURL,
                params={"registration": registration}
            )

            data = response.json() if response.status_code == 200 else None

        if data != None:
            photos=data["photos"]
        else:
            photos=None

        return render_template(
            "operatoredit.html",
            page_title = f"Edit ({operator.icao})",
            operator=operator,
            photos=photos,
            user=session["user"],
            registration=f"{aircraft.registration_prefix}-{aircraft.registration}" if operator.aircrafts else None,
            number = len(operator.aircrafts)
        )

    @app.route("/database/operator/<operator_id>/delete")
    def deleteoperator(operator_id):
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True:
                abort(403)
            operator=Operator.query.get(operator_id)
            if operator is None:
                abort(404)
            db.session.delete(operator)
            db.session.commit()
            return redirect(url_for("dboperator"))

    @app.route("/database/manufacturers")
    def manufacturer():
        manufacturers = Manufacturer.query.order_by(Manufacturer.manufacturer_name).all()
        if "user" in session:
            return render_template(
                "manufacturers.html",
                page_title = "Database (Manufacturers)",
                user=session["user"],
                manufacturers=manufacturers
            )
        else:
            return redirect(url_for("login"))
    
    @app.route("/logout")
    def logout():
        session.pop("user", None)
        return redirect(url_for("home"))
        
    return app
        
app = create_app()

@app.context_processor
def inject_user():
   if "user" in session:
       user=User.query.filter_by(username=session["user"]).first()
       is_admin = user is not None and user.admin is True
   else:
       is_admin = False

   return{
       "logged_in": "user" in session,
       "is_admin":  is_admin
   }

if __name__ == "__main__":
    app.run(debug = True, host = "127.0.0.1", port = 5000)
