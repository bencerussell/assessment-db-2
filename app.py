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
    registration = db.Column(db.String(10), primary_key = True)
    year_produced = db.Column(db.String(4), nullable = True)
    aircraft_icao = db.Column(db.String(5), nullable = False)
    operator_id = db.Column(db.String(3), db.ForeignKey("operator.icao"), nullable=False)
    registration_prefix = db.Column(db.String(5), db.ForeignKey("registration_prefix.prefix"), nullable=False)

    operator = db.relationship(
        "Operator",
        back_populates = "aircrafts"
    )

    prefix = db.relationship(
        "RegistrationPrefix",
        back_populates = "aircraft"
    )

class RegistrationPrefix(db.Model):
    __tablename__ = "registration_prefix"

    prefix = db.Column(db.String(10), primary_key = True)
    country_name = db.Column(db.String(50), nullable = False)
    country_id = db.Column(db.String(3), nullable = False)

    aircraft = db.relationship(
        "Aircraft",
        back_populates = "prefix"
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

        if Operator.query.count() == 0:
            op1 = Operator(icao="AAL", hub_icao="KDFW", year_founded=1930, operator_name="American Airlines")
            op2 = Operator(icao="DAL", hub_icao="KATL", year_founded=1924, operator_name="Delta Airlines")
            op3 = Operator(icao="UAL", hub_icao="KORD", year_founded=1926, operator_name="United Airlines")
            op4 = Operator(icao="SWA", hub_icao="KDAL", year_founded=1967, operator_name="Southwest Airlines")
            op5 = Operator(icao="NIL", hub_icao="N/A", year_founded=0, operator_name="Privately Owned")

            db.session.add_all([op1, op2, op3, op4, op5])
            db.session.commit()

        if RegistrationPrefix.query.count() == 0:
            prefixes = [
                {"prefix": "YA", "country_name": "Afghanistan", "country_id": "AFG"},
                {"prefix": "ZA", "country_name": "Albania", "country_id": "ALB"},
                {"prefix": "7T", "country_name": "Algeria", "country_id": "DZA"},
                {"prefix": "C3", "country_name": "Andorra", "country_id": "AND"},
                {"prefix": "D2", "country_name": "Angola", "country_id": "AGO"},
                {"prefix": "VP-A", "country_name": "Anguilla", "country_id": "AIA"},
                {"prefix": "V2", "country_name": "Antigua and Barbuda", "country_id": "ATG"},
                {"prefix": "LV", "country_name": "Argentina", "country_id": "ARG"},
                {"prefix": "LQ", "country_name": "Argentina", "country_id": "ARG"},
                {"prefix": "EK", "country_name": "Armenia", "country_id": "ARM"},
                {"prefix": "P4", "country_name": "Aruba", "country_id": "ABW"},
                {"prefix": "VH", "country_name": "Australia", "country_id": "AUS"},
                {"prefix": "OE", "country_name": "Austria", "country_id": "AUT"},
                {"prefix": "4K", "country_name": "Azerbaijan", "country_id": "AZE"},

                # B
                {"prefix": "C6", "country_name": "Bahamas", "country_id": "BHS"},
                {"prefix": "A9C", "country_name": "Bahrain", "country_id": "BHR"},
                {"prefix": "S2", "country_name": "Bangladesh", "country_id": "BGD"},
                {"prefix": "8P", "country_name": "Barbados", "country_id": "BRB"},
                {"prefix": "EW", "country_name": "Belarus", "country_id": "BLR"},
                {"prefix": "OO", "country_name": "Belgium", "country_id": "BEL"},
                {"prefix": "V3", "country_name": "Belize", "country_id": "BLZ"},
                {"prefix": "TY", "country_name": "Benin", "country_id": "BEN"},
                {"prefix": "VP-B", "country_name": "Bermuda", "country_id": "BMU"},
                {"prefix": "VQ-B", "country_name": "Bermuda", "country_id": "BMU"},
                {"prefix": "A5", "country_name": "Bhutan", "country_id": "BTN"},
                {"prefix": "CP", "country_name": "Bolivia", "country_id": "BOL"},
                {"prefix": "E7", "country_name": "Bosnia and Herzegovina", "country_id": "BIH"},
                {"prefix": "A2", "country_name": "Botswana", "country_id": "BWA"},
                {"prefix": "PP", "country_name": "Brazil", "country_id": "BRA"},
                {"prefix": "PR", "country_name": "Brazil", "country_id": "BRA"},
                {"prefix": "PS", "country_name": "Brazil", "country_id": "BRA"},
                {"prefix": "PT", "country_name": "Brazil", "country_id": "BRA"},
                {"prefix": "PU", "country_name": "Brazil", "country_id": "BRA"},
                {"prefix": "VP-LV", "country_name": "British Virgin Islands", "country_id": "VGB"},
                {"prefix": "V8", "country_name": "Brunei", "country_id": "BRN"},
                {"prefix": "LZ", "country_name": "Bulgaria", "country_id": "BGR"},
                {"prefix": "XT", "country_name": "Burkina Faso", "country_id": "BFA"},
                {"prefix": "9U", "country_name": "Burundi", "country_id": "BDI"},

                # C
                {"prefix": "XU", "country_name": "Cambodia", "country_id": "KHM"},
                {"prefix": "TJ", "country_name": "Cameroon", "country_id": "CMR"},
                {"prefix": "C", "country_name": "Canada", "country_id": "CAN"},
                {"prefix": "CF", "country_name": "Canada", "country_id": "CAN"},
                {"prefix": "CG", "country_name": "Canada", "country_id": "CAN"},
                {"prefix": "D4", "country_name": "Cape Verde", "country_id": "CPV"},
                {"prefix": "VP-C", "country_name": "Cayman Islands", "country_id": "CYM"},
                {"prefix": "TL", "country_name": "Central African Republic", "country_id": "CAF"},
                {"prefix": "TT", "country_name": "Chad", "country_id": "TCD"},
                {"prefix": "CC", "country_name": "Chile", "country_id": "CHL"},
                {"prefix": "B", "country_name": "China", "country_id": "CHN"},
                {"prefix": "HK", "country_name": "Colombia", "country_id": "COL"},
                {"prefix": "D6", "country_name": "Comoros", "country_id": "COM"},
                {"prefix": "TN", "country_name": "Congo (Brazzaville)", "country_id": "COG"},
                {"prefix": "9Q", "country_name": "Congo (Kinshasa)", "country_id": "COD"},
                {"prefix": "E5", "country_name": "Cook Islands", "country_id": "COK"},
                {"prefix": "TI", "country_name": "Costa Rica", "country_id": "CRI"},
                {"prefix": "TU", "country_name": "Cote d'Ivoire", "country_id": "CIV"},
                {"prefix": "9A", "country_name": "Croatia", "country_id": "HRV"},
                {"prefix": "CU", "country_name": "Cuba", "country_id": "CUB"},
                {"prefix": "5B", "country_name": "Cyprus", "country_id": "CYP"},
                {"prefix": "OK", "country_name": "Czech Republic", "country_id": "CZE"},

                # D & E
                {"prefix": "OY", "country_name": "Denmark", "country_id": "DNK"},
                {"prefix": "J2", "country_name": "Djibouti", "country_id": "DJI"},
                {"prefix": "J7", "country_name": "Dominica", "country_id": "DMA"},
                {"prefix": "HI", "country_name": "Dominican Republic", "country_id": "DOM"},
                {"prefix": "HC", "country_name": "Ecuador", "country_id": "ECU"},
                {"prefix": "SU", "country_name": "Egypt", "country_id": "EGY"},
                {"prefix": "YS", "country_name": "El Salvador", "country_id": "SLV"},
                {"prefix": "3C", "country_name": "Equatorial Guinea", "country_id": "GNQ"},
                {"prefix": "E3", "country_name": "Eritrea", "country_id": "ERI"},
                {"prefix": "ES", "country_name": "Estonia", "country_id": "EST"},
                {"prefix": "3D", "country_name": "Eswatini", "country_id": "SWZ"},
                {"prefix": "ET", "country_name": "Ethiopia", "country_id": "ETH"},

                # F & G
                {"prefix": "VP-F", "country_name": "Falkland Islands", "country_id": "FLK"},
                {"prefix": "DQ", "country_name": "Fiji", "country_id": "FJI"},
                {"prefix": "OH", "country_name": "Finland", "country_id": "FIN"},
                {"prefix": "F", "country_name": "France", "country_id": "FRA"},
                {"prefix": "TR", "country_name": "Gabon", "country_id": "GAB"},
                {"prefix": "C5", "country_name": "Gambia", "country_id": "GMB"},
                {"prefix": "4L", "country_name": "Georgia", "country_id": "GEO"},
                {"prefix": "D", "country_name": "Germany", "country_id": "DEU"},
                {"prefix": "9G", "country_name": "Ghana", "country_id": "GHA"},
                {"prefix": "VP-G", "country_name": "Gibraltar", "country_id": "GIB"},
                {"prefix": "SX", "country_name": "Greece", "country_id": "GRC"},
                {"prefix": "J3", "country_name": "Grenada", "country_id": "GRD"},
                {"prefix": "TG", "country_name": "Guatemala", "country_id": "GTM"},
                {"prefix": "3X", "country_name": "Guinea", "country_id": "GIN"},
                {"prefix": "J5", "country_name": "Guinea-Bissau", "country_id": "GNB"},
                {"prefix": "8R", "country_name": "Guyana", "country_id": "GUY"},

                # H & I
                {"prefix": "HH", "country_name": "Haiti", "country_id": "HTI"},
                {"prefix": "HR", "country_name": "Honduras", "country_id": "HND"},
                {"prefix": "B-H", "country_name": "Hong Kong", "country_id": "HKG"},
                {"prefix": "B-K", "country_name": "Hong Kong", "country_id": "HKG"},
                {"prefix": "B-L", "country_name": "Hong Kong", "country_id": "HKG"},
                {"prefix": "HA", "country_name": "Hungary", "country_id": "HUN"},
                {"prefix": "TF", "country_name": "Iceland", "country_id": "ISL"},
                {"prefix": "VT", "country_name": "India", "country_id": "IND"},
                {"prefix": "PK", "country_name": "Indonesia", "country_id": "IDN"},
                {"prefix": "EP", "country_name": "Iran", "country_id": "IRN"},
                {"prefix": "YI", "country_name": "Iraq", "country_id": "IRQ"},
                {"prefix": "EI", "country_name": "Ireland", "country_id": "IRL"},
                {"prefix": "EJ", "country_name": "Ireland", "country_id": "IRL"},
                {"prefix": "M", "country_name": "Isle of Man", "country_id": "IMN"},
                {"prefix": "4X", "country_name": "Israel", "country_id": "ISR"},
                {"prefix": "I", "country_name": "Italy", "country_id": "ITA"},

                # J & K
                {"prefix": "6Y", "country_name": "Jamaica", "country_id": "JAM"},
                {"prefix": "JA", "country_name": "Japan", "country_id": "JPN"},
                {"prefix": "JY", "country_name": "Jordan", "country_id": "JOR"},
                {"prefix": "UP", "country_name": "Kazakhstan", "country_id": "KAZ"},
                {"prefix": "5Y", "country_name": "Kenya", "country_id": "KEN"},
                {"prefix": "T3", "country_name": "Kiribati", "country_id": "KIR"},
                {"prefix": "P", "country_name": "North Korea", "country_id": "PRK"},
                {"prefix": "HL", "country_name": "South Korea", "country_id": "KOR"},
                {"prefix": "9K", "country_name": "Kuwait", "country_id": "KWT"},
                {"prefix": "EX", "country_name": "Kyrgyzstan", "country_id": "KGZ"},

                # L & M
                {"prefix": "RDPL", "country_name": "Laos", "country_id": "LAO"},
                {"prefix": "YL", "country_name": "Latvia", "country_id": "LVA"},
                {"prefix": "OD", "country_name": "Lebanon", "country_id": "LBN"},
                {"prefix": "7P", "country_name": "Lesotho", "country_id": "LSO"},
                {"prefix": "EL", "country_name": "Liberia", "country_id": "LBR"},
                {"prefix": "5A", "country_name": "Libya", "country_id": "LBY"},
                {"prefix": "HB-L", "country_name": "Liechtenstein", "country_id": "LIE"},
                {"prefix": "LY", "country_name": "Lithuania", "country_id": "LTU"},
                {"prefix": "LX", "country_name": "Luxembourg", "country_id": "LUX"},
                {"prefix": "B-M", "country_name": "Macau", "country_id": "MAC"},
                {"prefix": "5R", "country_name": "Madagascar", "country_id": "MDG"},
                {"prefix": "7Q", "country_name": "Malawi", "country_id": "MWI"},
                {"prefix": "9M", "country_name": "Malaysia", "country_id": "MYS"},
                {"prefix": "8Q", "country_name": "Maldives", "country_id": "MDV"},
                {"prefix": "TZ", "country_name": "Mali", "country_id": "MLI"},
                {"prefix": "9H", "country_name": "Malta", "country_id": "MLT"},
                {"prefix": "V7", "country_name": "Marshall Islands", "country_id": "MHL"},
                {"prefix": "5T", "country_name": "Mauritania", "country_id": "MRT"},
                {"prefix": "3B", "country_name": "Mauritius", "country_id": "MUS"},
                {"prefix": "XA", "country_name": "Mexico", "country_id": "MEX"},
                {"prefix": "XB", "country_name": "Mexico", "country_id": "MEX"},
                {"prefix": "XC", "country_name": "Mexico", "country_id": "MEX"},
                {"prefix": "V6", "country_name": "Micronesia", "country_id": "FSM"},
                {"prefix": "ER", "country_name": "Moldova", "country_id": "MDA"},
                {"prefix": "3A", "country_name": "Monaco", "country_id": "MCO"},
                {"prefix": "JU", "country_name": "Mongolia", "country_id": "MNG"},
                {"prefix": "4O", "country_name": "Montenegro", "country_id": "MNE"},
                {"prefix": "VP-M", "country_name": "Montserrat", "country_id": "MSR"},
                {"prefix": "CN", "country_name": "Morocco", "country_id": "MAR"},
                {"prefix": "C9", "country_name": "Mozambique", "country_id": "MOZ"},
                {"prefix": "XY", "country_name": "Myanmar", "country_id": "MMR"},

                # N & O & P
                {"prefix": "V5", "country_name": "Namibia", "country_id": "NAM"},
                {"prefix": "C2", "country_name": "Nauru", "country_id": "NRU"},
                {"prefix": "9N", "country_name": "Nepal", "country_id": "NPL"},
                {"prefix": "PH", "country_name": "Netherlands", "country_id": "NLD"},
                {"prefix": "PJ", "country_name": "Curaçao", "country_id": "CUW"},
                {"prefix": "ZK", "country_name": "New Zealand", "country_id": "NZL"},
                {"prefix": "ZL", "country_name": "New Zealand", "country_id": "NZL"},
                {"prefix": "ZM", "country_name": "New Zealand", "country_id": "NZL"},
                {"prefix": "YN", "country_name": "Nicaragua", "country_id": "NIC"},
                {"prefix": "5U", "country_name": "Niger", "country_id": "NER"},
                {"prefix": "5N", "country_name": "Nigeria", "country_id": "NGA"},
                {"prefix": "Z3", "country_name": "North Macedonia", "country_id": "MKD"},
                {"prefix": "LN", "country_name": "Norway", "country_id": "NOR"},
                {"prefix": "A4O", "country_name": "Oman", "country_id": "OMN"},
                {"prefix": "AP", "country_name": "Pakistan", "country_id": "PAK"},
                {"prefix": "T1", "country_name": "Palau", "country_id": "PLW"},
                {"prefix": "HP", "country_name": "Panama", "country_id": "PAN"},
                {"prefix": "P2", "country_name": "Papua New Guinea", "country_id": "PNG"},
                {"prefix": "ZP", "country_name": "Paraguay", "country_id": "PRY"},
                {"prefix": "OB", "country_name": "Peru", "country_id": "PER"},
                {"prefix": "RP", "country_name": "Philippines", "country_id": "PHL"},
                {"prefix": "SP", "country_name": "Poland", "country_id": "POL"},
                {"prefix": "CS", "country_name": "Portugal", "country_id": "PRT"},
                {"prefix": "CR", "country_name": "Portugal", "country_id": "PRT"},

                # Q & R & S
                {"prefix": "A7", "country_name": "Qatar", "country_id": "QAT"},
                {"prefix": "YR", "country_name": "Romania", "country_id": "ROU"},
                {"prefix": "RA", "country_name": "Russia", "country_id": "RUS"},
                {"prefix": "9XR", "country_name": "Rwanda", "country_id": "RWA"},
                {"prefix": "V4", "country_name": "Saint Kitts and Nevis", "country_id": "KNA"},
                {"prefix": "J6", "country_name": "Saint Lucia", "country_id": "LCA"},
                {"prefix": "J8", "country_name": "Saint Vincent and the Grenadines", "country_id": "VCT"},
                {"prefix": "5W", "country_name": "Samoa", "country_id": "WSM"},
                {"prefix": "T7", "country_name": "San Marino", "country_id": "SMR"},
                {"prefix": "S9", "country_name": "Sao Tome and Principe", "country_id": "STP"},
                {"prefix": "HZ", "country_name": "Saudi Arabia", "country_id": "SAU"},
                {"prefix": "6V", "country_name": "Senegal", "country_id": "SEN"},
                {"prefix": "6W", "country_name": "Senegal", "country_id": "SEN"},
                {"prefix": "YU", "country_name": "Serbia", "country_id": "SRB"},
                {"prefix": "S7", "country_name": "Seychelles", "country_id": "SYC"},
                {"prefix": "9L", "country_name": "Sierra Leone", "country_id": "SLE"},
                {"prefix": "9V", "country_name": "Singapore", "country_id": "SGP"},
                {"prefix": "OM", "country_name": "Slovakia", "country_id": "SVK"},
                {"prefix": "S5", "country_name": "Slovenia", "country_id": "SVN"},
                {"prefix": "H4", "country_name": "Solomon Islands", "country_id": "SLB"},
                {"prefix": "6O", "country_name": "Somalia", "country_id": "SOM"},
                {"prefix": "ZS", "country_name": "South Africa", "country_id": "ZAF"},
                {"prefix": "ZT", "country_name": "South Africa", "country_id": "ZAF"},
                {"prefix": "ZU", "country_name": "South Africa", "country_id": "ZAF"},
                {"prefix": "Z8", "country_name": "South Sudan", "country_id": "SSD"},
                {"prefix": "EC", "country_name": "Spain", "country_id": "ESP"},
                {"prefix": "4R", "country_name": "Sri Lanka", "country_id": "LKA"},
                {"prefix": "ST", "country_name": "Sudan", "country_id": "SDN"},
                {"prefix": "PZ", "country_name": "Suriname", "country_id": "SUR"},
                {"prefix": "SE", "country_name": "Sweden", "country_id": "SWE"},
                {"prefix": "HB", "country_name": "Switzerland", "country_id": "CHE"},
                {"prefix": "YK", "country_name": "Syria", "country_id": "SYR"},

                # T & U & V
                {"prefix": "EY", "country_name": "Tajikistan", "country_id": "TJK"},
                {"prefix": "5H", "country_name": "Tanzania", "country_id": "TZA"},
                {"prefix": "HS", "country_name": "Thailand", "country_id": "THA"},
                {"prefix": "5V", "country_name": "Togo", "country_id": "TGO"},
                {"prefix": "A3", "country_name": "Tonga", "country_id": "TON"},
                {"prefix": "9Y", "country_name": "Trinidad and Tobago", "country_id": "TTO"},
                {"prefix": "TS", "country_name": "Tunisia", "country_id": "TUN"},
                {"prefix": "TC", "country_name": "Turkey", "country_id": "TUR"},
                {"prefix": "EZ", "country_name": "Turkmenistan", "country_id": "TKM"},
                {"prefix": "VQ-T", "country_name": "Turks and Caicos Islands", "country_id": "TCA"},
                {"prefix": "T2", "country_name": "Tuvalu", "country_id": "TUV"},
                {"prefix": "5X", "country_name": "Uganda", "country_id": "UGA"},
                {"prefix": "UR", "country_name": "Ukraine", "country_id": "UKR"},
                {"prefix": "A6", "country_name": "United Arab Emirates", "country_id": "ARE"},
                {"prefix": "G", "country_name": "United Kingdom", "country_id": "GBR"},
                {"prefix": "N", "country_name": "United States", "country_id": "USA"},
                {"prefix": "CX", "country_name": "Uruguay", "country_id": "URY"},
                {"prefix": "UK", "country_name": "Uzbekistan", "country_id": "UZB"},

                # Y & Z
                {"prefix": "YJ", "country_name": "Vanuatu", "country_id": "VUT"},
                {"prefix": "HV", "country_name": "Vatican City", "country_id": "VAT"},
                {"prefix": "YV", "country_name": "Venezuela", "country_id": "VEN"},
                {"prefix": "VN", "country_name": "Vietnam", "country_id": "VNM"},
                {"prefix": "7O", "country_name": "Yemen", "country_id": "YEM"},
                {"prefix": "9J", "country_name": "Zambia", "country_id": "ZMB"},
                {"prefix": "Z", "country_name": "Zimbabwe", "country_id": "ZWE"},
            ]

            db.session.add_all(prefixes)
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

    @app.route("/db-add", methods=["GET", "POST"])
    def db_add():
        type = None
        operators = Operator.query.order_by(Operator.operator_name).all()
        prefixes = Registration.query.order_by(Registration.prefix).all()
        if "user" in session:
            if request.method == "POST":
                action = request.form["action"]

                if action == "aircraft":
                    type="aircraft"
                elif action == "operator":
                    type="operator"
                elif action == "submit_aircraft":
                    registration = request.form["registration"]
                    country = request.form["country"]
                    year_produced = request.form["year_produced"]
                    aircraft_icao = request.form["icao"]
                    operator_id = request.form["operator_id"]

                    new_aircraft = Aircraft(
                        registration=registration,
                        country=country,
                        year_produced=year_produced,
                        aircraft_icao=aircraft_icao,
                        operator_id=operator_id
                    )

                    db.session.add(new_aircraft)
                    db.session.commit()

                    return redirect(url_for("dashboard"))
            
            return render_template(
                "db-add.html",
                page_title = "Add to the Database",
                type=type,
                operators=operators,
                prefixes=prefixes
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
