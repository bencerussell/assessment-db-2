from flask import Flask, render_template, abort, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
import csv, requests, random, datetime, string

APIURL = "http://127.0.0.1:8787"

db = SQLAlchemy()

# --ALL TABLES RELATING TO THE DATABASE--

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25), unique = True, nullable = False)
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
    operator_name = db.Column(db.String(50), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = True)
    date_time = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)
    callsign = db.Column(db.String(50), nullable=False)

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

    aircrafts = db.relationship(
        "Aircraft",
        back_populates = "manufacturer"
    )

class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    registration = db.Column(db.String(5), nullable = False)
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
            op5 = Operator(icao="NIL", hub_icao="NONE", year_founded=0, operator_name="Privately Owned", user_id=1, callsign="N/A")

            db.session.add_all([op5, op1, op2, op3, op4]) # Adds the 5 previously defined operators
            db.session.commit()

    @app.route("/")
    def home():
        aircraft_data =[]

        aircrafts = Aircraft.query.order_by(Aircraft.id.desc()).all()

        for aircraft in aircrafts:
            if len(aircraft_data) >= 3: # Checks if the total aircraft (to display on the home page) is still less than 3
                break
            prefix = aircraft.registration_prefix
            if prefix not in ["N", "JA", "HL", "VP-A", "VP-B", "VQ-B"]: # Ensures correct registration formatting
                registration = f"{prefix}-{aircraft.registration}"
            else:
                registration = f"{prefix}{aircraft.registration}"

            try:
                response = requests.get(APIURL, params={"registration": registration}, timeout=3) # Gets registration from jetphotos API
                data=response.json() if response.status_code == 200 else None 
            except requests.exceptions.RequestException:
                data=None

            if data and "photos" in data and len(data["photos"]) > 0:
                    aircraft_data.append({"aircraft":aircraft, "photo":data["photos"][0]}) # Adds photo & aircraft to the table if it has a photo

        count=Aircraft.query.count() # Counts number of aircraft in the database for the home screen display

        return render_template(
            "home.html",
            page_title = "Home",
            greeting = "Welcome to AeroBase",
            aircraft_data=aircraft_data,
            count=count
            )
        
    @app.route("/about-us")
    def about_us():
        return render_template(
            "about-us.html",
            page_title = "About Us",
            )
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        create_account = False

        if request.method == "POST":
            action = request.form["action"]

            if action == "create": # action == "create" when someone selects that they want to create an account, rather than redirecting them to a new page. This reloads the page to show the create_account options on the page.
                create_account = True 
            elif action == "loginreturn":
                create_account = False
            elif action == "actualcreate": # action == "actualcreate" when someone actually clicks 'create account' after inputting their information.
                create_account = True

                username = request.form["username"].lower().strip()
                password = request.form["password"].strip()
                email = request.form["email"].strip()
                confirmpassword = request.form["confirm_password"].strip()

                if len(email) > 254: # checks email length within sql parameters
                    flash("Email must be less than 254 characters", "error") 
                elif email.count("@") != 1 or "." not in email.split("@")[1]: # checks email is valid
                    flash("Email is invalid", "error")
                elif User.query.filter_by(email=email).first(): # checks if email is already in use
                    flash("Email already in use", "error") 
                elif len(username) < 3 or len(username) > 25: # checks if username length within sql parameters
                    flash("Username must be between 3 and 25 characters", "error")
                elif User.query.filter_by(username=username).first(): # checks if username is already in use
                    flash("Username already in use", "error")
                elif any(char in string.punctuation for char in username): # checks username doesnt have special character
                    flash("Username cannot contain special characters", "error")
                elif username.strip() != username.replace(" ", ""): # checks username doesnt have spaces
                    flash("Username cannot contain spaces", "error")
                elif password != confirmpassword: # checks if passwords match
                    flash("Passwords do not match", "error")
                elif len(password) < 8 or len(password) > 100: # checks password length
                    flash("Password must be between 8 and 100 characters", "error")
                elif not any(char in string.punctuation for char in password): # checks password has at least one special character
                    flash("Password must contain at least one special character", "error")

                else: # if none of the above apply
                    new_user = User(
                        username=username,
                        email=email,
                        password=generate_password_hash(password) # uses werkzeug to convert a string to a secure encrypted hash
                    )

                    db.session.add(new_user)
                    db.session.commit()

                    session["user"] = username # logs user in after creating account
                    
                    next_page = request.args.get("next") # If users have been redirected to login from an original page, it will redirect them to the original page

                    if not next_page:
                        next_page = url_for("home") # If the above is not met, users will be redirected to the home page

                    flash("Account created successfully", "success")

                    return redirect(next_page) # Does the actual redirecting

            elif action == "login":
                username = request.form["username"].lower().strip()
                password = request.form["password"].strip()

                user = User.query.filter_by(username=username).first()

                next_page = request.args.get("next") # Redirects them to the previous page they were on (from where they were prompted to login)

                if user and check_password_hash(user.password, password):
                    session["user"] = username
                    if not next_page:
                        next_page = url_for("home")

                    return redirect(next_page)
                else:
                    flash("Invalid username or password", "error")

        return render_template(
            "login.html",
            page_title = "Login",
            create_account=create_account
        )
    
    @app.route("/profile")
    def profile():
        if "user" in session: # Checks if the user is logged in
            user = User.query.filter_by(username=session["user"]).first() # Pulls user's information from database

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
        if "user" in session: # Checks if user is logged in 
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
        manufacturers = Manufacturer.query.order_by(Manufacturer.manufacturer_name).all() # Pulls a list of all manufacturers (in reality aircraft type ICAOs) to use in a <select> HTML function
        if "user" in session:
            if request.method == "POST":
                action = request.form["action"]

                # following if statements check what button was pressed (no redirection)

                if action == "aircraft": # if the user wants to add an aircraft
                    type="aircraft"
                elif action == "operator": # if the user wants to add an operator
                    type="operator"
                elif action == "submit_aircraft": # if the user is submitting an aircraft to the database
                    type = "aircraft"
                    try:
                        year_produced = int(request.form["year_produced"]) # tries to convert the year to a number - if this doesn't work it removes the year
                    except ValueError:
                        year_produced = None

                    registration = request.form["registration"].upper().strip()
                    prefix = request.form["prefix"]
                    aircraft_icao = request.form["icao"].upper()
                    operator_id = request.form["operator_id"]
                    user_id = User.query.filter_by(username=session["user"]).first().id
                    
                    if Aircraft.query.filter_by(registration=registration, registration_prefix=prefix).first(): # restarts the process if registration already exists
                        flash("Aircraft with this registration already exists", "error")
                    elif len(registration) > 5:
                        flash("Registration must be less than 6 characters", "error") # ensures compliance with sql 
                    elif any(char in string.punctuation for char in registration): # checks registration doesnt have special character
                        flash("Registration cannot contain special characters", "error")
                    elif year_produced is not None and year_produced > datetime.datetime.now().year:
                        flash("Year of production cannot be in the future", "error")
                    elif year_produced is not None and year_produced < 1903: # checks year produced isnt before the wright brothers
                        flash("Year of production cannot be before 1903", "error")
                    elif registration == '' or registration is None: # checks registration isnt blank
                        flash("Registration cannot be blank", "error")
                    else: # adds the aircraft to the database if none of the above conditions are met
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

                        flash("Aircraft saved successfully", "success")

                        return redirect(url_for("aircraftdetail", aircraft_id=new_aircraft.id))
                elif action == "submit_operator": # if the user is submitting a new operator to the database
                    type = "operator"
                    try:
                        year_founded = int(request.form["year"]) # checks if year founded is a number
                    except ValueError:
                        year_founded = None # turns year founded to nothing to use below
                    icao = request.form["icao"].upper().strip()
                    hub_icao = request.form["hub"].upper().strip()
                    operator_name = request.form["name"].title().strip()
                    user_id = User.query.filter_by(username=session["user"]).first().id
                    callsign=request.form["callsign"].title() .strip()

                    if len(icao) != 3: # checks icao is 3 letters
                        flash("ICAO must be 3 characters", "error")
                    elif Operator.query.filter_by(icao=icao).first(): # checks icao isnt duplicate
                        flash("Operator with the same ICAO already exists", "error")
                    elif any(char.isdigit() for char in icao): # checks icao doesnt have numbers
                        flash("ICAO code cannot contain numbers", "error")
                    elif any(char in string.punctuation for char in icao): # checks icao doesnt have special character
                        flash("ICAO code cannot contain special characters", "error")
                    elif len(hub_icao) != 4: # checks hub is 4 letters
                        flash("Hub ICAO must be 4 characters", "error")
                    elif any(char.isdigit() for char in hub_icao): # checks hub doesnt have numbers
                        flash("Hub ICAO cannot contain numbers", "error")
                    elif any(char in string.punctuation for char in hub_icao): # checks hub icao doesnt have special character
                        flash("Hub ICAO code cannot contain special characters", "error")
                    elif year_founded is None: # checks year founded is inputted
                        flash("Year founded is invalid", "error") 
                    elif year_founded > datetime.datetime.today().year: # checks year founded isnt in the future
                        flash("Year founded cannot be in the future", "error")
                    elif year_founded < 1909: # checks year founded isnt before the first airline
                        flash("Year founded cannot be before 1909", "error")
                    elif len(operator_name) > 50: # checks operator name is less than 50 characters
                        flash("Operator name cannot be over 50 characters", "error")
                    elif Operator.query.filter_by(operator_name=operator_name).first(): # checks operator name doesnt already exist
                        flash("Operator with the same name already exists", "error")
                    elif any(char in string.punctuation for char in operator_name): # checks operator name doesnt have special character
                        flash("Operator name cannot contain special characters", "error")
                    elif len(callsign) > 50: # checks callsign is less than 50 characters
                        flash("Callsign must be less than 50 characters", "error")
                    elif Operator.query.filter_by(callsign=callsign).first(): # checks that callsign doesnt already exist
                        flash("Operator with the same callsign already exists", "error")
                    elif any(char in string.punctuation for char in callsign): # checks callsign doesnt have special character
                        flash("Callsign cannot contain special characters", "error")
                    elif operator_name == '' or operator_name is None: # checks operator name isnt blank
                        flash("Operator name cannot be blank", "error")
                    elif callsign == '' or callsign is None: # checks callsign isnt blank
                        flash("Callsign cannot be blank", "error")
                    else: # adds the operator to the database if success
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

                        flash("Operator saved successfully", "success")

                        return redirect(url_for("operatordetail", operator_id=icao))
            
            return render_template(
                "db-add.html",
                page_title = "Add to the Database",
                type=type,
                operators=operators,
                prefixes=prefixes,
                manufacturers=manufacturers
            )
        else:
            return redirect(url_for("login", next=request.url)) # redirects the user if not logged in 

    @app.route("/database")
    def database():
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
        q = request.args.get("q", '').strip() # checks the htmx search query
        offset=request.args.get("offset", 0, type=int)
        limit=50 # limit of aircraft initially displayed at a time

        query=Aircraft.query
        
        if q:
            search_filter = [ # configures the different things people can search by
                (Aircraft.registration_prefix + "-" + Aircraft.registration).ilike(f"%{q}%") |
                Aircraft.operator.has(
                    Operator.operator_name.ilike(f"%{q}%")
                ) |
                Aircraft.manufacturer.has(
                    Manufacturer.model_name.ilike(f"%{q}%") |
                    Manufacturer.type_icao.ilike(f"%{q}%") |
                    Manufacturer.manufacturer_name.ilike(f"%{q}%")
                )
            ] 

            if q.isdigit():
                search_filter.append(Aircraft.year_produced == int(q)) # adds year to the filter if search is given a number

            query = query.filter(or_(*search_filter))

        total = query.count() # total count in the search

        aircraft=query.order_by(Aircraft.id.desc()).limit(offset+limit).all() # collects search results

        if request.headers.get("HX-Request"): # returns and adds aircraft to the table from a htmx request (the search bar)
            return render_template(
                "aircraft-table.html",
                aircrafts=aircraft,
                total=total,
                q=q,
            )
        if "user" in session:
            return render_template(
                "aircraft.html",
                page_title = "Database (Aircraft)",
                user=session["user"],
                aircrafts=aircraft,
                total=total,
                offset=offset # offset is used if the user loads extra aircraft ('load 50 more')
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/aircraft/<aircraft_id>") # Redirects to the selected aircraft ID (from the database page)
    def aircraftdetail(aircraft_id):
        aircraft = Aircraft.query.get(aircraft_id) # Locates the aircraft in the database from the ID
        if aircraft is None:
            abort(404) # Aborts if it cannot find the aircraft in order to prevent further errors appearing
        prefix = aircraft.registration_prefix
        if prefix not in ["N", "JA", "HL", "VP-A", "VP-B", "VQ-B"]: # correct registration formatting
            registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
        else:  
            registration = f"{aircraft.registration_prefix}{aircraft.registration}"

        try:
            response = requests.get(APIURL, params={"registration": registration}, timeout=3) # Gets registration from jetphotos API
            data=response.json() if response.status_code == 200 else None 
        except requests.exceptions.RequestException:
            data=None

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
        if "user" in session:
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True: # ensures the user is an admin
                abort(403)
            aircraft=Aircraft.query.get(aircraft_id)
            if aircraft is None:
                abort(404)
            db.session.delete(aircraft) # deletes the aircraft
            db.session.commit()

            flash("Aircraft deleted successfully", "success")
            return redirect(url_for("dbaircraft"))
        else:
            return redirect(url_for("login"))

    @app.route("/database/aircraft/<aircraft_id>/edit", methods=["GET", "POST"])
    def editaircraft(aircraft_id):
        if "user" in session:
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True: # checks user is an admin
                abort(403)
            aircraft=Aircraft.query.get(aircraft_id)
            operators = Operator.query.order_by(Operator.operator_name).all() # Pulls a list of all operators to use in a <select> HTML function
            prefixes = RegistrationPrefix.query.order_by(RegistrationPrefix.prefix).all() # Pulls a list of all registration prefixes to use in a <select> HTML function 
            manufacturers = Manufacturer.query.order_by(Manufacturer.type_icao).all() # Pulls a list of all manufacturers (in reality aircraft type ICAOs) to use in a <select> HTML function

            if aircraft is None:
                abort(404)

            prefix = aircraft.registration_prefix
            if prefix not in ["N", "JA", "HL", "VP-A", "VP-B", "VQ-B"]: # correct registration formatting
                registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
            else:  
                registration = f"{aircraft.registration_prefix}{aircraft.registration}"

            try:
                response = requests.get(APIURL, params={"registration": registration}, timeout=3) # Gets registration from jetphotos API
                data=response.json() if response.status_code == 200 else None 
            except requests.exceptions.RequestException:
                data=None

            if request.method == "POST":
                action = request.form["action"]

                if action == "saveedit": # checks when the admin has saved the aircraft's edits
                    try:
                        year_produced = int(request.form["year_produced"])
                    except ValueError:
                        year_produced = None

                    aircraft_icao = request.form["icao"].upper().strip()
                    operator_id = request.form["operator_id"].strip()
                    user_id = User.query.filter_by(username=session["user"]).first().id

                    if year_produced is not None and year_produced > datetime.datetime.now().year:
                        flash("Year of production cannot be in the future", "error")
                    elif year_produced is not None and year_produced < 1903: # checks year produced isnt before the wright brothers
                        flash("Year of production cannot be before 1903", "error")
                    else:
                        aircraft.manufacturer_id = aircraft_icao
                        aircraft.operator_id = operator_id
                        aircraft.year_produced = year_produced
                        aircraft.user_id = user_id
                        db.session.commit() # saves the edits to the database

                        flash("Aircraft saved successfully", "success")

                        return redirect(url_for("aircraftdetail", aircraft_id=aircraft_id))

            return render_template(
                "aircraftedit.html",
                page_title=f"Edit ({aircraft.registration_prefix}-{aircraft.registration})",
                aircraft=aircraft,
                operators=operators,
                manufacturers=manufacturers,
                photos=data["photos"] if data else None
            )
        else:
            return redirect(url_for("login"))


    @app.route("/database/operators")
    def dboperator():
        operators = Operator.query.order_by(Operator.operator_name).all() # collects all operators to display in the table
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
        if "user" in session:
            operator=Operator.query.get(operator_id)
            data = None
            if operator is None:
                abort(404)

            if operator.aircrafts:
                aircraft = random.choice(operator.aircrafts) # picks a random aircraft from the operator to display a photo of
                prefix = aircraft.registration_prefix
                if prefix not in ["N", "JA", "HL", "VP-A", "VP-B", "VQ-B"]: # correct registration formatting
                        registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
                else:  
                    registration = f"{aircraft.registration_prefix}{aircraft.registration}"
                try:
                    response = requests.get(APIURL, params={"registration": registration}, timeout=3) # Gets registration from jetphotos API
                    data=response.json() if response.status_code == 200 else None 
                except requests.exceptions.RequestException:
                    data=None

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
                number = len(operator.aircrafts), # counts number of aircraft that the operator has
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/operators/<operator_id>/edit", methods=["GET", "POST"])
    def operatoredit(operator_id):
        if "user" in session:
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True: # checks user is an admin
                abort(403)
            if operator_id == "NIL": # can't delete privately owned
                abort(403)
            operator=Operator.query.get(operator_id)
            data = None
            if operator is None: # checks the operator actually exists
                abort(404)

            if not operator.aircrafts:
                photo = None
            else:
                aircraft = random.choice(operator.aircrafts) # displays random photo from the operator
                prefix = aircraft.registration_prefix
                if prefix not in ["N", "JA", "HL", "VP-A", "VP-B", "VQ-B"]: # correct registration formatting
                        registration = f"{aircraft.registration_prefix}-{aircraft.registration}"
                else:  
                    registration = f"{aircraft.registration_prefix}{aircraft.registration}"
                try:
                    response = requests.get(APIURL, params={"registration": registration}, timeout=3) # Gets registration from jetphotos API
                    data=response.json() if response.status_code == 200 else None 
                except requests.exceptions.RequestException:
                    data=None

            if data != None:
                photos=data["photos"]
            else:
                photos=None

            if request.method == "POST":
                action = request.form["action"]

                if action == "saveoperator": # checks when the admin has saved the operator's edits
                    try:
                        year_founded = int(request.form["year"])
                    except ValueError:
                        year_founded = None
                    hub_icao = request.form["hub"].upper().strip()
                    operator_name = request.form["name"].title().strip()
                    callsign=request.form["callsign"].title().strip()

                    if len(hub_icao) != 4: # checks hub is 4 letters
                        flash("Hub ICAO must be 4 characters", "error")
                    elif any(char.isdigit() for char in hub_icao): # checks hub doesnt have numbers
                        flash("Hub ICAO cannot contain numbers", "error")
                    elif any(char in string.punctuation for char in hub_icao): # checks hub icao doesnt have special character
                        flash("Hub ICAO code cannot contain special characters", "error")
                    elif year_founded is None: # checks if year has been made an integer
                        flash("Year founded is invalid", "error")
                    elif year_founded > datetime.datetime.today().year: # checks year founded isnt in the future
                        flash("Year founded cannot be in the future", "error")
                    elif year_founded < 1909: # checks year founded isnt before the first airline
                        flash("Year founded cannot be before 1909", "error")
                    elif len(operator_name) > 50: # checks operator name is less than 50 characters
                        flash("Operator name cannot be over 50 characters", "error")
                    elif any(char in string.punctuation for char in operator_name): # checks operator name doesnt have special character
                        flash("Operator name cannot contain special characters", "error")
                    elif len(callsign) > 50: # checks callsign is less than 50 characters
                        flash("Callsign must be less than 50 characters", "error")
                    elif any(char in string.punctuation for char in callsign): # checks callsign doesnt have special character
                        flash("Callsign cannot contain special characters", "error")
                    elif operator_name == '' or operator_name is None: # checks operator name isnt blank
                        flash("Operator name cannot be blank", "error")
                    elif callsign == '' or callsign is None: # checks callsign isnt blank
                        flash("Callsign cannot be blank", "error")
                    else:
                        operator.hub_icao = hub_icao
                        operator.year_founded = year_founded
                        operator.operator_name = operator_name
                        operator.callsign=callsign
                        db.session.commit() # saves the edits to the database

                        flash("Operator saved successfully", "success")

                        return redirect(url_for("operatordetail", operator_id=operator_id))

            return render_template(
                "operatoredit.html",
                page_title = f"Edit ({operator.icao})",
                operator=operator,
                photos=photos,
                user=session["user"],
                registration=f"{aircraft.registration_prefix}-{aircraft.registration}" if operator.aircrafts else None,
                number = len(operator.aircrafts)
            )
        else:
            return redirect(url_for("login"))

    @app.route("/database/operators/<operator_id>/delete")
    def deleteoperator(operator_id):
        if "user" in session:
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True: # checks user is an admin
                abort(403)
            operator=Operator.query.get(operator_id)
            if operator is None:
                abort(404)
            if aircraft := Aircraft.query.filter_by(operator_id=operator.icao).first(): # checks operator doesnt have any aircraft belonging to it
                flash("Cannot delete operator with associated aircraft.", "error")
                return redirect(url_for("operatordetail", operator_id=operator_id))
            db.session.delete(operator)
            db.session.commit()
            flash("Operator deleted successfully", "success") # confirms the operator has been deleted
            return redirect(url_for("dboperator"))
        else:
            return redirect(url_for("login"))
    
    @app.route("/logout")
    def logout():
        session.pop("user", None) # logs user out
        return redirect(url_for("home"))

    @app.route("/admin")
    def admin():
        if "user" in session:
            if not User.query.filter_by(username=session["user"]).first() or User.query.filter_by(username=session["user"]).first().admin != True: # checks user is an admin
                abort(403)
            users = User.query.order_by(User.id) # pulls all users

            return render_template(
                "admin.html",
                page_title = "Admin",
                users=users
            )
        else:
            return redirect(url_for("login")) 
    
    @app.route("/admin/user/<int:user_id>/admin", methods=["POST"])
    def update_admin(user_id): # updates the 'admin' field for a user based on the checkbox on the admin page
        if "user" in session:
            current_user = User.query.filter_by(username=session["user"]).first()
            if not current_user or not current_user.admin:
                abort(403)
            user = User.query.get_or_404(user_id)
            data = request.get_json()
            user.admin = data["admin"]
            db.session.commit()
            return "", 204
        else:
            return redirect(url_for("login"))

    @app.route("/admin/user/<int:user_id>/delete")
    def delete_user(user_id):
        if "user" in session:
            current_user = User.query.filter_by(username=session["user"]).first()
            if not current_user or not current_user.admin:
                abort(403)
            user = User.query.get_or_404(user_id)
            if not user.admin:
                db.session.delete(user) # deletes target user
                db.session.commit()
                flash("User deleted successfully", "success")
            else:
                flash("User is an admin and cannot be deleted", "error")
            return redirect(url_for("admin"))
        else:
            return redirect(url_for("login"))
        
    return app
        
app = create_app()

@app.context_processor
def inject_user():
   if "user" in session: # checks if user is an admin (assuming they're logged in) to use in nav bar
       user=User.query.filter_by(username=session["user"]).first()
       is_admin = user is not None and user.admin is True
   else:
       is_admin = False

   return{
       "logged_in": "user" in session, # sends logged in to 'nav'
       "is_admin":  is_admin, # sends admin to 'nav'
       "version": "V0.5.0" # current version
   }

if __name__ == "__main__":
    app.run(debug = True, host = "127.0.0.1", port = 5000)
