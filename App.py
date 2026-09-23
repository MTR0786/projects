import os

from flask import Flask, render_template, redirect, request, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# DATABASE CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= USER TABLE =================


class User(db.Model):
    __tablename__ = "users"

    u_id = db.Column(db.Integer, primary_key=True)

    u_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    mobile_number = db.Column(
        db.String(10),
        unique = True,
        nullable = False
    )
    
    gmail = db.Column(
        db.String(100),
        unique = True,
        nullable = False
    )
    password = db.Column(
        db.String(100),
        nullable=False
    )

    # student / company
    role = db.Column(
        db.String(20),
        nullable=False
    )

    # only for staff
    is_approved = db.Column(
    db.Boolean,
    default=False
    )

    is_blacklisted = db.Column(db.Boolean, 
    default=False
    )

# ================= TREK TABLE =================
class Trek(db.Model):
    __tablename__="treks"

    trek_id = db.Column(db.Integer, primary_key=True)
    
    trek_name = db.Column(db.String(100), nullable = False)

    location = db.Column(db.String(100) , nullable=False)

    difficulty = db.Column(db.String(100) , nullable=False)

    duration = db.Column(db.String(50), nullable=False )

    available_slots = db.Column(db.Integer , nullable=False)

    start_date = db.Column(db.Date , nullable=False)

    end_date = db.Column(db.Date , nullable = False)

    status = db.Column(db.String(20), default="Open")

    description = db.Column(db.Text)

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.u_id")
    )



# ===============Booking Table ===============

class Booking(db.Model):
    __tablename__ = "bookings"

    booking_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.u_id"), nullable=False)

    u_name = db.Column(db.Integer,  )

    trek_id = db.Column(db.Integer, db.ForeignKey("treks.trek_id"), nullable=False)

    trek_name= db.Column(db.String(100), )

    booking_date = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(20), default="Booked")

    # number_of_people = db.Column( db.Integer, default=1 , nullable=False )



# ================= ROUTES =================

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        number =request.form['mobile_number']
        gmail = request.form['gmail']
        password = request.form['password']
        role = request.form['role']

        # #  Prevent admin registration
        # if role == "admin":
        #     flash("Admin registration is not allowed.", "error")
        #     return redirect('/register')

        # Check existing gmail
        existing_user = User.query.filter_by(
            gmail=gmail
        ).first()
        if existing_user:
            return "Gmail already exists"
        
        # check existing mobile number

        existing_number = User.query.filter_by(
            mobile_number = number
            ).first()
        if existing_number:
            return "Number already exists"
        
        #for approved status
        if role == "staff":
            approved=False
        else:
            approved=True

    #For push data into table
        new_user = User(
            u_name=username,
            mobile_number= number,
            gmail = gmail,
            password=password,
            role=role,
            is_approved = approved
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login' , methods=['GET' , 'POST' ,])
def login():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']
        role = request.form['role']

        user = User.query.filter_by(gmail = gmail).first()

        if user and user.password == password and user.role == role:

            session["user_id"] = user.u_id
            session["username"] = user.u_name
            session["role"] = user.role

            if role == 'trekker':
                flash("Login successful!", "success")
                return redirect('/trekker_dashboard')

            elif role == 'staff':
                if user.is_approved:
                    flash("Login successful!", "success")
                    return redirect('/staff_dashboard')
                else:
                    flash("Your account is waiting for admin approval.", "warning")
                    return redirect('/login')
                    
            elif role =='admin':
                flash("Login Successfull !", "success")
                return redirect('/admin_dashboard')
        
        flash("Invalid Gmail, Password, or Role", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("logout successfull","success")
    return redirect('/login')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/trekker_dashboard')
def trekker():

    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "trekker":
        return redirect('/login')

    # Get search values
    trek_name = request.args.get("trek_name", "").strip()
    location = request.args.get("location", "all").strip()
    difficulty = request.args.get("difficulty", "all").strip()

    # Start query
    treks = Trek.query.filter_by(status="Open")

    #trekker dashboard statistics

    total_open_treks = Trek.query.filter_by(status="Open").count()

    my_bookings = Booking.query.filter_by(
        user_id=session["user_id"],
        status="Booked"
    ).count()

    completed = Booking.query.join(Trek).filter(
    Booking.user_id == session["user_id"],
    Trek.status == "Completed"
    ).count()

    cancelled = Booking.query.filter_by(
        user_id=session["user_id"],
        status="Cancelled"
    ).count()

    # Search by Trek Name
    if trek_name:
        treks = treks.filter(
            Trek.trek_name.ilike(f"%{trek_name}%")
        )

    # Search by Location
    if location != "all":
        treks = treks.filter(
            Trek.location == location
        )

    # Search by Difficulty
    if difficulty != "all":
        treks = treks.filter(
            Trek.difficulty == difficulty
        )

    # Execute query
    treks = treks.all()

    # Get unique locations for dropdown
    locations = db.session.query(
        Trek.location
    ).filter_by(
        status="Open"
    ).distinct().all()

    return render_template(
        "trekker.html",
        treks=treks,
        locations=locations,
        total_open_treks=total_open_treks,
        my_bookings=my_bookings,
        completed_treks=completed,
        cancelled=cancelled,
    )

@app.route('/staff_dashboard')
def staff():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return redirect("/login")

    staff_id = session["user_id"]

    trek = Trek.query.filter_by(
        assigned_staff_id=staff_id
    ).first()

    if trek:
        trek_number = 1
        trek_status = trek.status
        participants = Booking.query.filter_by(trek_id=trek.trek_id, status ="Booked" ).count()
        slots = trek.available_slots
    else:
        trek_number = 0
        trek_status = "N/A"
        slots = "N/A"

    return render_template(
        "staff.html",
        trek=trek,
        trek_number=trek_number,
        trek_status=trek_status,
        no_of_participants = participants,
        slots=slots,
    )

@app.route('/admin_dashboard')
def admin():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")

    pending_staff = User.query.filter_by(
        role="staff",
        is_approved=False
    ).all()

  
#count admin statistics 
    total_staff = User.query.filter_by(role="staff").count()
    total_users = User.query.filter_by(role='trekker').count()

    # Until we create these models
    total_treks = Trek.query.filter_by(status='Open').count()
    total_bookings = Booking.query.filter_by(status='Booked').count()

    


    return render_template(
        "admin.html",
        pending_staff=pending_staff,
        total_staff=total_staff,
        total_bookings=total_bookings,
        total_trekkers=total_users,
        total_treks=total_treks
    )

@app.route('/approve_staff/<int:id>')
def approve_staff(id):

    if session.get("role") != "admin":
        return redirect("/login")

    staff = User.query.get_or_404(id)

    staff.is_approved = True

    db.session.commit()

    flash("Staff approved successfully!", "success")

    return redirect("/admin_dashboard")

    
@app.route('/add_trek',methods=['POST','GET'])
def add_trek():
    # Only admin can access
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")
    
    if request.method=='POST':
        
        trek_name = request.form['trek_name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        duration = request.form['duration']
        available_slots = request.form['available_slots']
        start_date = datetime.strptime(
            request.form['start_date'],
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            request.form['end_date'],
            "%Y-%m-%d"
        ).date()

        status = request.form['status']
        description = request.form['description']

        new_trek = Trek(
            trek_name=trek_name,          
            location=location,
            difficulty=difficulty,
            duration=duration,
            available_slots=available_slots,
            start_date=start_date,
            end_date=end_date,
            status=status,
            description=description

            # assigned_staff_id will be assigned later
        )
        db.session.add(new_trek)
        db.session.commit()

        flash("Trek Added Successfully!", "success")

        return redirect("/manage_treks")

    return render_template('add_trek.html')


@app.route('/manage_treks')
def manage_treks():
    # Only admin can access
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")

    treks = Trek.query.all()

    return render_template('manage_trek.html' ,
                           treks=treks
                           )


@app.route('/edit_trek/<int:trek_id>', methods=['GET', 'POST'])
def edit_trek(trek_id):

    # Only admin can edit
    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "admin":
        return redirect('/login')

    # Find the trek
    trek = Trek.query.get_or_404(trek_id)

    # When Update button is clicked
    if request.method == "POST":

        trek.trek_name = request.form['trek_name']
        trek.location = request.form['location']
        trek.difficulty = request.form['difficulty']
        trek.duration = request.form['duration']
        trek.available_slots = request.form['available_slots']

        trek.start_date = datetime.strptime(
            request.form['start_date'],
            "%Y-%m-%d"
        ).date()

        trek.end_date = datetime.strptime(
            request.form['end_date'],
            "%Y-%m-%d"
        ).date()

        trek.status = request.form['status']
        trek.description = request.form['description']

        
        db.session.commit()

        flash("Trek updated successfully!", "success")

        return redirect('/manage_treks')

    return render_template(
        "edit_trek.html",
        trek=trek
    )

@app.route('/staff_edit_trek/<int:trek_id>', methods=['GET', 'POST'])
def staff_edit_trek(trek_id):

# Only staff can execces
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return redirect("/login")

    # Find the trek
    staff_id = session["user_id"]

    trek = Trek.query.filter_by(
        trek_id=trek_id,
        assigned_staff_id=staff_id
    ).first()

    if not trek:
        flash("No trek assigned to you.", "error")
        return redirect("/staff_dashboard")

    # When Update button is clicked
    if request.method == "POST":

        trek.difficulty = request.form['difficulty']
        trek.duration = request.form['duration']
        trek.available_slots = request.form['available_slots']

        trek.start_date = datetime.strptime(
            request.form['start_date'],
            "%Y-%m-%d"
        ).date()

        trek.end_date = datetime.strptime(
            request.form['end_date'],
            "%Y-%m-%d"
        ).date()

        trek.status = request.form['status']

        
        db.session.commit()

        flash("Trek updated successfully!", "success")

        return redirect('/staff_dashboard')

    return render_template(
        "staff_edit_trek.html",
        trek=trek
    )

@app.route('/delete_trek/<int:trek_id>')
def delete_trek(trek_id):
    # Only admin can edit
    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "admin":
        return redirect('/login')
    
    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)

    db.session.commit()

    flash("Trek deleted successfully!", "success")

    return redirect('/manage_treks')

    
@app.route('/assign_staff/<int:trek_id>')
def assign_staff(trek_id):

     # Only admin can edit
    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "admin":
        return redirect('/login')

# get all approved staff
    staffs = User.query.filter_by( role='staff', is_approved=True ).all()

#get selected trek
    trek = Trek.query.get_or_404(trek_id)

    for staff in staffs:
        assigned = Trek.query.filter_by(assigned_staff_id=staff.u_id).first()
        if assigned:
            staff.assignment_status = "Already Assigned"
        else:
            staff.assignment_status = "Not Assigned"

    return render_template('assign_staff.html',staffs=staffs , trek=trek )


@app.route('/save_assign_staff/<int:trek_id>/<int:staff_id>', methods=['GET','POST'])
def save_assign_staff(trek_id, staff_id):

    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "admin":
        return redirect('/login')

    trek = Trek.query.get_or_404(trek_id)

    trek.assigned_staff_id = staff_id

    db.session.commit()

    flash("Staff assigned successfully!", "success")

    return redirect('/manage_treks')


@app.route('/manage_staff')
def manage_staff():
   #check admin login or not 
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")
    
    users= User.query.filter(User.role == "staff" and User.is_approved ==True )

    search = request.args.get("search")
    if search:
        if search.isdigit():
            users = users.filter(
                User.u_id == int(search)
            )
        else:
            users = users.filter(
                User.u_name.ilike(f"%{search}%")
            )
    users = users.all()

    return render_template('manage_staff.html' , users= users)

@app.route('/manage_trekker')
def manage_trekker():
    #check admin login or not 
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")
    
    users= User.query.filter(User.role == "trekker" )

    search = request.args.get("search")
    if search:
        if search.isdigit():
            users = users.filter(
                User.u_id == int(search)
            )
        else:
            users = users.filter(
                User.u_name.ilike(f"%{search}%")
            )
    users = users.all()

    return render_template('manage_trekker.html' , users = users)


@app.route("/activate_user/<int:u_id>")
def activate_user(u_id):
#check admin login 
    if "user_id" not in session:
        return redirect("/login")
    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(u_id)
    user.is_blacklisted = False
    db.session.commit()
    flash("Staff activated successfully.", "success")

    if user.role == "satff":
        return redirect(url_for("manage_staff"))
    else:
        return redirect(url_for("manage_trekker"))
    

@app.route("/blacklist_user/<int:u_id>")
def blacklist_user(u_id):
    #check admin login
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/login")

    user = User.query.get_or_404(u_id)

    user.is_blacklisted = True
    db.session.commit()

    flash("Staff blacklisted successfully.", "success")

    if user.role == "staff":
        return redirect(url_for("manage_staff"))
    else:
        return redirect(url_for("manage_trekker"))
    
@app.route('/manage_booking')
def manage_booking():
    # Check login
    if "user_id" not in session:
        return redirect('/login')
    role = session.get("role")

    # ---------------- ADMIN ----------------
    if role == "admin":
      bookings = Booking.query.all()

    # ---------------- STAFF ----------------
    elif role == "staff":
        trek = Trek.query.filter_by(
            assigned_staff_id=session["user_id"]
        ).first()
        if trek:
            bookings = Booking.query.filter_by(
                trek_id=trek.trek_id
            ).all()
        else:
            bookings = []
    else:
        return redirect('/login')

    # ---------- SEARCH ----------

    search = request.args.get("search")
    if search:
        search = search.lower()
        bookings = [
            booking for booking in bookings
            if search in str(booking.booking_id).lower()
            or search in str(booking.user_id).lower()
            or search in str(booking.u_name).lower()
            or search in str(booking.trek_id).lower()
            or search in str(booking.trek_name).lower()
        ]

    return render_template(
        "manage_booking.html",
        bookings=bookings
    )

@app.route('/manage_cancel_booking/<int:booking_id>', methods=['POST'])
def manage_cancel_booking(booking_id):
    if "user_id" not in session:
        return redirect('/login')
    booking = Booking.query.get_or_404(booking_id)

    # Already cancelled
    if booking.status == "Cancelled":
        flash("Booking is already cancelled.", "warning")
        return redirect('/manage_booking')
    
    trek = Trek.query.get(booking.trek_id)

    booking.status = "Cancelled"

    trek.available_slots += 1
    db.session.commit()

    flash("Booking cancelled successfully.", "success")

    return redirect('/manage_booking')

@app.route('/booking/<int:trek_id>' , methods=['GET' , 'POST'])
def booking(trek_id):
    # check trekker is booking
    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "trekker":
        return redirect('/login')

    trek = Trek.query.get_or_404(trek_id)

    booking_date = date.today()

#check available treks
    if trek.available_slots <= 0:
        flash("No seats available for this trek.", "error")
        return redirect('/trekker_dashboard')

# check is user booked alredy ?
    existing_booking = Booking.query.filter_by(
    user_id=session["user_id"],
    trek_id=trek_id,
    status="Booked"
    ).first()

    if existing_booking:
        flash("You have already booked this trek.", "error")
        return redirect('/trekker_dashboard')

    if request.method=="POST":
        new_booking = Booking(
            user_id=session["user_id"],
            u_name = session["username"],
            trek_id=trek_id,
            trek_name= trek.trek_name,
            booking_date=date.today(),
            status="Booked"
            )
        db.session.add(new_booking)
        db.session.commit()

        trek.available_slots -= 1

        return redirect('/trekker_dashboard')

    return render_template('/booking.html' ,
                    trek=trek,
                    booking_date =booking_date ,
                      )
    
@app.route('/my_bookings')
def my_bookings():

    # Check login
    if "user_id" not in session:
        return redirect('/login')

    # Only trekkers
    if session.get("role") != "trekker":
        return redirect('/login')
    
    bookings = Booking.query.filter_by(
    user_id=session["user_id"],
    status="Booked"
    ).all()

    booking_data = []

    for booking in bookings:
        trek = Trek.query.get(booking.trek_id)
        booking_data.append({
            "booking": booking,
            "trek": trek
        })

    return render_template(
        "my_booking.html",
        booking_data=booking_data
    )

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):

    # Check login
    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "trekker":
        return redirect('/login')

    booking = Booking.query.get_or_404(booking_id)

    # Security: ensure users can only cancel their own bookings
    if booking.user_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        return redirect('/my_bookings')

    # Get the associated trek
    trek = Trek.query.get(booking.trek_id)

    # Increase available slots
    trek.available_slots += 1

    # Mark booking as cancelled
    booking.status = "Cancelled"

    db.session.commit()

    flash("Booking cancelled successfully.", "success")

    return redirect('/my_bookings')
# ================= CREATE DATABASE =================

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(role="admin").first()

    if not admin:
        admin = User(
            u_name="Administrator",
            mobile_number="9999999999",
            gmail="admin@gmail.com",
            password="admin123",
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print("Default Admin Created")

# ================= RUN APP =================

if __name__ == '__main__':
    app.run(debug=True)