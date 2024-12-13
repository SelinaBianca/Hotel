import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('hotel_management.db')
cursor = conn.cursor()


# Create Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    userID INTEGER PRIMARY KEY,
    name VARCHAR(255),
    username VARCHAR(255),
    email VARCHAR(255),
    password_hash TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    phone_number VARCHAR(100),
    nic VARCHAR(255),
    created_at DATETIME
)
''')

# Create Rooms table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Rooms (
    roomID INTEGER PRIMARY KEY,
    room_number VARCHAR(50),
    room_type VARCHAR(100) ,
    description TEXT,
    price_per_night REAL,
    availability BOOLEAN
)
''')

# Create Services table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Services (
    serviceID INTEGER PRIMARY KEY,
    service_name VARCHAR(255),
    description TEXT,
    price REAL
)
''')

# Create BookingServices table
cursor.execute('''
CREATE TABLE IF NOT EXISTS BookingServices (
    bookingServiceID INTEGER PRIMARY KEY,
    bookingID INTEGER,
    serviceID INTEGER,
    FOREIGN KEY (bookingID) REFERENCES Bookings(bookingID),
    FOREIGN KEY (serviceID) REFERENCES Services(serviceID)
)
''')

# Create Chatbot table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Chatbot (
    ID INTEGER PRIMARY KEY,
    userID INTEGER,
    message TEXT,
    response TEXT,
    timestamp DATETIME,
    FOREIGN KEY (userID) REFERENCES Users(userID)
)
''')

# Create Offers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Offers (
    offerID INTEGER PRIMARY KEY,
    title VARCHAR(255),
    image BLOB,
    created_at DATETIME,
    valid_from DATETIME,
    valid_to DATETIME
)
''')

# Create NewsAlerts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS NewsAlerts (
    newsID INTEGER PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    image BLOB,
    created_at DATETIME
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS RoomImages (
    imageID INTEGER PRIMARY KEY AUTOINCREMENT,
    roomID INTEGER,
    image BLOB,
    FOREIGN KEY (roomID) REFERENCES Rooms(roomID)
)
''')

cursor.execute('DROP TABLE IF EXISTS RoomImages')


cursor.execute('''
CREATE TABLE IF NOT EXISTS RoomImages (
    imageID INTEGER PRIMARY KEY AUTOINCREMENT,
    roomID INTEGER,
    image_path TEXT,
    FOREIGN KEY (roomID) REFERENCES Rooms(roomID)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Bookings (
    bookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    roomID INTEGER,
    serviceID TEXT,
    payment_Slip VARCHAR(50),
    check_in DATETIME,
    check_out DATETIME,
    no_adults INTEGER,
    no_kids INTEGER,
    name VARCHAR(255),
    surname VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    booking_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Confirmed',  -- Set the default value as 'Confirmed'
    FOREIGN KEY (roomID) REFERENCES Rooms(roomID)
);
''')


# Drop the existing Rooms table
cursor.execute('DROP TABLE IF EXISTS Rooms')



# Create a new Rooms table with an additional 'capacity' column
cursor.execute('''
CREATE TABLE IF NOT EXISTS Rooms (
    roomID INTEGER PRIMARY KEY,
    room_number VARCHAR(50),
    room_type VARCHAR(100),
    description TEXT,
    price_per_night REAL,
    availability BOOLEAN,
    capacity INTEGER
)
''')


cursor.execute('DROP TABLE IF EXISTS Bookings;')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Bookings (
    bookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    roomID INTEGER,
    serviceID TEXT,
    total_price INTEGER,
    check_in DATETIME,
    check_out DATETIME,
    no_adults INTEGER,
    no_kids INTEGER,
    name VARCHAR(255),
    surname VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(50),
    booking_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Confirmed',
    FOREIGN KEY (roomID) REFERENCES Rooms(roomID)
);
''')




# Commit the changes and close the connection
conn.commit()
conn.close()

