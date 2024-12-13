from flask import Flask, render_template, request, jsonify,redirect, url_for, session, flash
import base64
import sqlite3
import secrets
import random
import string
import re
import uuid
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy





app = Flask(__name__ , static_folder='static')
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'payment_slips')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'selinafer2004@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'yyotpcxhqnpycqpg'
app.config['MAIL_DEFAULT_SENDER'] = 'selinafer2004@gmail.com'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

mail = Mail(app)




class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    no_adults = db.Column(db.Integer, nullable=False)
    no_kids = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    room = db.relationship('Room', back_populates='bookings')



# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect('hotel_management.db')
    conn.row_factory = sqlite3.Row
    return conn



# -------------------------------------------------------------------------------------------------------------------------



@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/Experience')
def experience_page():
    return render_template('experience.html')


@app.route('/Chatbot')
def chatbot():
    return render_template('chatbot.html')





# -------------------------------------------------------------------------------------------------------------------------

# Function to validate email format
def is_valid_email(email):
    # Regex pattern for validating email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

# Function to validate password complexity
def is_valid_password(password):
    # Password must contain at least 8 characters, 1 uppercase, 1 lowercase, 1 digit, 1 special character
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'[0-9]', password) or
        not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        return False
    return True

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        # Validate email format
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return render_template('signup.html')

        # Validate password complexity
        if not is_valid_password(password):
            flash('Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character', 'error')
            return render_template('signup.html')

        # Check if username or email already exists
        conn = get_db_connection()
        try:
            existing_user = conn.execute(
                'SELECT * FROM Users WHERE username = ? OR email = ?', (username, email)
            ).fetchone()
            if existing_user:
                flash('Username or email already exists', 'error')
                return render_template('signup.html')

            # Hash the password
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')

            # Insert new user
            conn.execute(
                'INSERT INTO Users (name, username, email, password_hash) VALUES (?, ?, ?, ?)',
                (name, username, email, password_hash)
            )
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
        finally:
            conn.close()

        # Redirect to login page
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['userID']
            session['is_admin'] = user['is_admin']
            flash('Login successful!', 'success')
            return redirect(url_for('admin_panel' if user['is_admin'] else 'home'))

        flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
            if user:
                token = secrets.token_urlsafe()
                reset_url = url_for('reset_password', token=token, _external=True)

                # Send the reset email
                msg = Message('Password Reset Request', recipients=[email])
                msg.body = f'Click the link to reset your password: {reset_url}'
                try:
                    mail.send(msg)
                    flash('A password reset link has been sent to your email.', 'info')
                except Exception as e:
                    flash(f'Error sending email: {str(e)}', 'error')
            else:
                flash('Email not found.', 'error')
        finally:
            conn.close()

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form['password']
        conn = get_db_connection()

        # Here you should validate the token and find the associated user
        # For example:
        # user = conn.execute('SELECT * FROM Users WHERE token = ?', (token,)).fetchone()

        # Assuming user is found:
        try:
            hashed_password = generate_password_hash(new_password)
            conn.execute('UPDATE Users SET password_hash = ? WHERE email = ?', (hashed_password,user['email']))
            conn.commit()
            flash('Your password has been updated!', 'success')
        except Exception as e:
            flash(f'Error updating password: {str(e)}', 'error')
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

# -------------------------------------------------------------------------------------------------------------------------

@app.route('/dashboard')
def admin_panel():
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# -------------------------------------------------------------------------------------------------------------------------

@app.route('/home')
def home():
    if not session.get('user_id'):
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    return render_template('home.html')

# -------------------------------------------------------------------------------------------------------------------------

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home_page'))

# -------------------------------------------------------------------------------------------------------------------------

# View all users
@app.route('/users')
def view_users():
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM Users').fetchall()
    conn.close()

    return render_template('view_users.html', users=users)

# -------------------------------------------------------------------------------------------------------------------------

# Edit user
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM Users WHERE userID = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        # Get updated details from the form
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        is_admin = request.form.get('is_admin') == 'on'

        # Update user in the database
        conn.execute(
            'UPDATE Users SET name = ?, username = ?, email = ?, is_admin = ? WHERE userID = ?',
            (name, username, email, is_admin, user_id)
        )
        conn.commit()
        conn.close()

        flash('User updated successfully!', 'success')
        return redirect(url_for('view_users'))

    conn.close()
    return render_template('edit_user.html', user=user)


# Delete user
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM Users WHERE userID = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('view_users'))

# -------------------------------------------------------------------------------------------------------------------------
# Routes for Room Management
# -------------------------------------------------------------------------------------------------------------------------
# Route to display the admin panel for rooms
@app.route('/admin/rooms', methods=['GET'])
def admin_rooms():
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Fetch all rooms and their images
    cursor = conn.execute('SELECT * FROM Rooms')
    rooms = cursor.fetchall()

    cursor = conn.execute('''
        SELECT Rooms.roomID, RoomImages.image_path 
        FROM RoomImages 
        JOIN Rooms ON RoomImages.roomID = Rooms.roomID
    ''')
    room_images = cursor.fetchall()

    conn.close()
    return render_template('admin_rooms.html', rooms=rooms, room_images=room_images)

# -------------------------------------------------------------------------------------------------------------------------
# Route to handle room creation
# -------------------------------------------------------------------------------------------------------------------------
@app.route('/admin/rooms/create', methods=['GET', 'POST'])
def create_room():
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        room_number = request.form.get('room_number')
        room_type = request.form.get('room_type')
        description = request.form.get('description')
        price_per_night = request.form.get('price_per_night')
        availability = request.form.get('availability') == 'on'
        capacity = request.form.get('capacity')  # Get the capacity from the form

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert room into the database including capacity
        cursor.execute('''
            INSERT INTO Rooms (room_number, room_type, description, price_per_night, availability, capacity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_number, room_type, description, float(price_per_night), availability, int(capacity)))  # Include capacity
        conn.commit()

        # Get the ID of the newly created room
        room_id = cursor.lastrowid

        # Handle image upload
        images = request.files.getlist('images')  # Allows multiple image uploads
        for image in images:
            if image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                cursor.execute('''
                    INSERT INTO RoomImages (roomID, image_path)
                    VALUES (?, ?)
                ''', (room_id, filename))

        conn.commit()
        conn.close()
        flash('Room created successfully!', 'success')
        return redirect(url_for('admin_rooms'))

    return render_template('create_rooms.html')


@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the room details for editing
    cursor.execute('SELECT * FROM Rooms WHERE roomID = ?', (room_id,))
    room = cursor.fetchone()

    if not room:
        flash('Room not found!', 'error')
        return redirect(url_for('admin_rooms'))

    if request.method == 'POST':
        room_number = request.form.get('room_number')
        room_type = request.form.get('room_type')
        description = request.form.get('description')
        price_per_night = request.form.get('price_per_night')
        availability = request.form.get('availability') == 'on'
        capacity = request.form.get('capacity')  # Get the updated capacity from the form

        # Update room details, including capacity
        cursor.execute('''
            UPDATE Rooms
            SET room_number = ?, room_type = ?, description = ?, price_per_night = ?, availability = ?, capacity = ?
            WHERE roomID = ?
        ''', (room_number, room_type, description, float(price_per_night), availability, int(capacity), room_id))  # Include capacity

        conn.commit()
        conn.close()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('admin_rooms'))

    conn.close()
    return render_template('edit_room.html', room=room)




# Route to handle room deletion
@app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if not session.get('is_admin'):
        flash('Unauthorized access. Admins only!', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete room and associated images
    cursor.execute('DELETE FROM RoomImages WHERE roomID = ?', (room_id,))
    cursor.execute('DELETE FROM Rooms WHERE roomID = ?', (room_id,))
    conn.commit()
    conn.close()

    flash('Room deleted successfully!', 'success')
    return redirect(url_for('admin_rooms'))

# -------------------------------------------------------------------------------------------------------------------------
# Route to list all services
# -------------------------------------------------------------------------------------------------------------------------
@app.route('/services')
def list_services():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM Services').fetchall()
    conn.close()
    return render_template('services.html', services=services)

# Route to add a new service
@app.route('/services/add', methods=('GET', 'POST'))
def add_service():
    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        price = request.form['price']

        if not service_name or not price:
            flash('Service name and price are required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO Services (service_name, description, price) VALUES (?, ?, ?)',
                         (service_name, description, price))
            conn.commit()
            conn.close()
            flash('Service added successfully!')
            return redirect(url_for('list_services'))

    return render_template('add_service.html')

# Route to edit an existing service
@app.route('/services/edit/<int:serviceID>', methods=('GET', 'POST'))
def edit_service(serviceID):
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM Services WHERE serviceID = ?', (serviceID,)).fetchone()

    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        price = request.form['price']

        if not service_name or not price:
            flash('Service name and price are required!')
        else:
            conn.execute('UPDATE Services SET service_name = ?, description = ?, price = ? WHERE serviceID = ?',
                         (service_name, description, price, serviceID))
            conn.commit()
            conn.close()
            flash('Service updated successfully!')
            return redirect(url_for('list_services'))

    conn.close()
    return render_template('edit_service.html', service=service)

# Route to delete a service
@app.route('/services/delete/<int:serviceID>', methods=('POST',))
def delete_service(serviceID):
    conn = get_db_connection()
    conn.execute('DELETE FROM Services WHERE serviceID = ?', (serviceID,))
    conn.commit()
    conn.close()
    flash('Service deleted successfully!')
    return redirect(url_for('list_services'))
# -------------------------------------------------------------------------------------------------------------------------
# Route to display all news alerts
# -------------------------------------------------------------------------------------------------------------------------

@app.route('/admin/news-alerts', methods=['GET'])
def manage_news_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM NewsAlerts')
    news_alerts = cursor.fetchall()
    conn.close()  # Ensure connection is closed after use
    return render_template('news_alerts.html', news_alerts=news_alerts)

# Route to create a new news alert
@app.route('/admin/news-alerts/create', methods=['GET', 'POST'])
def create_news_alert():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files['image'].read() if 'image' in request.files else None
        created_at = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO NewsAlerts (title, description, image, created_at) 
            VALUES (?, ?, ?, ?)
        ''', (title, description, image, created_at))
        conn.commit()
        conn.close()
        flash('News alert created successfully!', 'success')
        return redirect(url_for('manage_news_alerts'))

    return render_template('create_news_alerts.html')

# Route to delete a news alert
@app.route('/admin/news-alerts/delete/<int:news_id>', methods=['POST'])
def delete_news_alert(news_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM NewsAlerts WHERE newsID = ?', (news_id,))
    conn.commit()
    conn.close()
    flash('News alert deleted successfully!', 'success')
    return redirect(url_for('manage_news_alerts'))



@app.route('/news', methods=['GET'])
def news():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM NewsAlerts')
    news_alerts = cursor.fetchall()

    conn.close()  # Ensure connection is closed after use
    return render_template('News.html', news_alerts=news_alerts)

@app.template_filter('b64encode')
def b64encode_filter(data):
    """Encode data to base64."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


# -------------------------------------------------------------------------------------------------------------------------
# Route to display the booking management page with rooms and bookings
# -------------------------------------------------------------------------------------------------------------------------

def generate_booking_number():
    """Generate a unique 5-digit booking number."""
    return 'HAH-' + ''.join(random.choices(string.digits, k=5))

@app.route('/bookings/create', methods=['GET', 'POST'])
def create_booking():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Rooms')
    rooms = cursor.fetchall()

    cursor.execute('SELECT * FROM Services')
    services = cursor.fetchall()

    if request.method == 'POST':
        booking_number = generate_booking_number()  # Generate booking number once

        # Get form data
        roomID = request.form.get('roomID')
        selected_service_ids = request.form.getlist('service_ids[]')
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        no_adults = request.form['no_adults']
        no_kids = request.form['no_kids']
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone_number = request.form['phone_number']
        total_price = request.form['total_price']
        status = 'confirmed'  # Set status

        try:
            # Insert into Bookings table
            cursor.execute('''
                INSERT INTO Bookings (roomID, check_in, check_out, no_adults, no_kids, name, surname, email, phone_number, booking_number, total_price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (roomID, check_in, check_out, no_adults, no_kids, name, surname, email, phone_number, booking_number, total_price, status))

            booking_id = cursor.lastrowid  # Get the last inserted bookingID

            # Insert into BookingServices for each selected service
            for service_id in selected_service_ids:
                cursor.execute('''
                    INSERT INTO BookingServices (bookingID, serviceID)
                    VALUES (?, ?)
                ''', (booking_id, service_id))

            conn.commit()  # Commit the transaction
            return redirect(url_for('manage_bookings'))

        except Exception as e:
            conn.rollback()  # Rollback in case of error
            flash('An error occurred while creating the booking. Please try again.')
            print(f"Error: {e}")  # Optional: Log the error

        finally:
            conn.close()

    return render_template('create_booking.html', rooms=rooms, services=services)

#-----------------------------------------------------------------------------------------------------------------------

@app.route('/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
def edit_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the booking details
    cursor.execute('SELECT * FROM Bookings WHERE bookingID = ?', (booking_id,))
    booking = cursor.fetchone()

    # Get available rooms and services
    cursor.execute('SELECT * FROM Rooms')
    rooms = cursor.fetchall()

    cursor.execute('SELECT * FROM Services')
    services = cursor.fetchall()

    # Get current services for the booking
    cursor.execute('SELECT serviceID FROM BookingServices WHERE bookingID = ?', (booking_id,))
    booking_service_ids = [row['serviceID'] for row in cursor.fetchall()]

    if request.method == 'POST':
        # Get form data safely
        roomID = request.form.get('roomID')
        selected_service_ids = request.form.getlist('service_ids[]')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        no_adults = request.form.get('no_adults')
        no_kids = request.form.get('no_kids')
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        total_price = request.form.get('total_price')
        status = request.form.get('status')  # Safely retrieve 'status' field

        # Update Bookings table
        cursor.execute('''
            UPDATE Bookings
            SET roomID = ?, check_in = ?, check_out = ?, no_adults = ?, no_kids = ?, 
                name = ?, surname = ?, email = ?, phone_number = ?, total_price = ?, status = ?
            WHERE bookingID = ?
        ''', (roomID, check_in, check_out, no_adults, no_kids, name, surname, email, phone_number, total_price, status, booking_id))

        # Update BookingServices (delete old ones and insert new ones)
        cursor.execute('DELETE FROM BookingServices WHERE bookingID = ?', (booking_id,))
        for service_id in selected_service_ids:
            cursor.execute('''
                INSERT INTO BookingServices (bookingID, serviceID)
                VALUES (?, ?)
            ''', (booking_id, service_id))

        conn.commit()
        conn.close()

        return redirect(url_for('manage_bookings'))

    conn.close()
    return render_template('edit_booking.html', booking=booking, rooms=rooms, services=services, booking_service_ids=booking_service_ids)

#-----------------------------------------------------------------------------------------------------------------------
@app.route('/manage_bookings', methods=['GET'])
def manage_bookings():
    connection = get_db_connection()
    bookings = connection.execute('''
        SELECT bookingID, roomID, serviceID, total_price, check_in, check_out, no_adults, no_kids, name, surname, email, phone_number, booking_number, created_at, status 
        FROM Bookings
    ''').fetchall()
    connection.close()

    return render_template('manage_bookings.html', bookings=bookings)

@app.route('/bookings/delete/<int:bookingID>', methods=['POST'])
def delete_booking(bookingID):
    conn = get_db_connection()
    conn.execute('DELETE FROM Bookings WHERE bookingID = ?', (bookingID,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_bookings'))


@app.route('/bookings/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the status to 'Cancelled'
    cursor.execute('''
        UPDATE Bookings
        SET status = 'Cancelled'
        WHERE bookingID = ?
    ''', (booking_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('manage_bookings'))


#-----------------------------------------------------------------------------------------------------------------------
#booking page
#-----------------------------------------------------------------------------------------------------------------------
@app.route('/Search for a room')
def reservation_page():
    return render_template('booking.html')

@app.route('/search', methods=['POST'])
def search_rooms():
    # Extract search parameters
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    no_adults = int(request.form.get('no_adults', 0))
    no_kids = int(request.form.get('no_kids', 0))
    total_guests = no_adults + no_kids

    connection = get_db_connection()

    # Query rooms based on capacity and availability
    query = """
    SELECT * FROM Rooms
    WHERE availability = 1
      AND (
          (room_type = 'Family Room' AND ? <= 4)
          OR (room_type = 'Double Room' AND ? <= 2)
      )
    """
    rooms = connection.execute(query, (total_guests, total_guests)).fetchall()
    connection.close()

    return render_template('results.html', rooms=rooms, check_in=check_in, check_out=check_out)


@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    if request.method == 'POST':
        # Collect user inputs
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        no_adults = int(request.form.get('no_adults', 0))
        no_kids = int(request.form.get('no_kids', 0))
        service_ids = request.form.getlist('service_ids')  # Fetch selected services

        connection = get_db_connection()

        # Calculate room price
        room = connection.execute('SELECT price_per_night FROM Rooms WHERE roomID = ?', (room_id,)).fetchone()
        price_per_night = room['price_per_night']
        total_nights = (datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days
        total_price = price_per_night * total_nights

        # Add service costs if selected
        service_costs = 0
        if service_ids:
            services = connection.execute('SELECT price FROM Services WHERE serviceID IN ({})'.format(
                ','.join('?' * len(service_ids))
            ), service_ids).fetchall()
            service_costs = sum(service['price'] for service in services)

        total_price += service_costs

        # Generate booking number
        booking_number = str(uuid.uuid4())[:8]

        cursor = connection.cursor()

        # Insert booking into the database
        cursor.execute('''
            INSERT INTO Bookings (roomID, serviceID, total_price, check_in, check_out, no_adults, no_kids, name, surname, email, phone_number, booking_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        room_id, ','.join(service_ids), total_price, check_in, check_out, no_adults, no_kids, name, surname, email,
        phone_number, booking_number))

        # Insert selected services into BookingServices table
        booking_id = cursor.lastrowid
        for service_id in service_ids:
            cursor.execute('''
                INSERT INTO BookingServices (bookingID, serviceID)
                VALUES (?, ?)
            ''', (booking_id, service_id))

        # Mark room as unavailable
        cursor.execute('UPDATE Rooms SET availability = 0 WHERE roomID = ?', (room_id,))

        connection.commit()
        connection.close()

        return render_template('booking_success.html', booking_id=booking_id)

    # Fetch room and services
    connection = get_db_connection()
    room = connection.execute('SELECT * FROM Rooms WHERE roomID = ?', (room_id,)).fetchone()
    services = connection.execute('SELECT * FROM Services').fetchall()
    connection.close()

    return render_template('book.html', room=room, services=services)



@app.route('/cancel-reservation', methods=['POST'])
def cancel_reservation():
    booking_id = request.form.get('booking_id')

    # Update booking status to 'Cancelled' in the database
    conn = get_db_connection()
    conn.execute('UPDATE Bookings SET status = ? WHERE bookingID = ?', ('Cancelled', booking_id))
    conn.commit()
    conn.close()

    flash('Your reservation has been canceled successfully.', 'success')
    return redirect(url_for('check_reservation'))

@app.route('/verify-reservation', methods=['GET', 'POST'])
def verify_reservation():
    if request.method == 'POST':
        surname = request.form.get('surname')
        booking_id = request.form.get('booking_id')

        # Database query to check if booking exists
        conn = sqlite3.connect('hotel_management.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Bookings WHERE surname=? AND bookingID=?", (surname, booking_id))
        reservation = cursor.fetchone()
        conn.close()

        if reservation:
            # Redirect to a details page with the reservation info
            return render_template('reservation_details.html', reservation=reservation)
        else:
            flash('Reservation not found. Please check your details and try again.', 'error')
            return redirect(url_for('verify_reservation'))

    return render_template('verify_reservation.html')



if __name__ == '__main__':
    app.run(debug=True)


