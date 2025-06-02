from flask import Flask, render_template, request, redirect, flash, url_for
import mysql.connector

app = Flask(__name__)
app.secret_key = "airline-secret"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@Vishu123",  # put your MySQL password here
    database="airlines",
    auth_plugin="mysql_native_password"
)
cursor = conn.cursor(dictionary=True)

def get_available_seats(flight_id):
    cursor.execute("SELECT Total_Seats FROM Aircraft a JOIN Flight f ON a.Aircraft_ID=f.Aircraft_ID WHERE f.FlightID=%s", (flight_id,))
    total = cursor.fetchone()["Total_Seats"]
    cursor.execute("SELECT COUNT(*) AS count FROM Booking WHERE FlightID=%s", (flight_id,))
    booked = cursor.fetchone()["count"]
    return total - booked

app.jinja_env.globals.update(get_available_seats=get_available_seats)

@app.route('/')
def home():
    return render_template('index.html')

# Passengers
@app.route('/passengers')
def passengers():
    cursor.execute("SELECT * FROM Passenger")
    return render_template('passengers.html', passengers=cursor.fetchall())

@app.route('/passenger/register', methods=['GET', 'POST'])
def passenger_register():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO Passenger (Name, Email, Phone, Passport_Number) VALUES (%s,%s,%s,%s)",
            (request.form['name'], request.form['email'], request.form['phone'], request.form['passport'])
        )
        conn.commit()
        flash('Passenger registered')
        return redirect(url_for('passengers'))
    return render_template('passenger_form.html')

# Flights
@app.route('/flights')
def flights():
    cursor.execute("SELECT f.*, a.Model FROM Flight f JOIN Aircraft a ON a.Aircraft_ID=f.Aircraft_ID")
    return render_template('flights.html', flights=cursor.fetchall())

@app.route('/flight/add', methods=['GET', 'POST'])
def flight_add():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO Flight (Flight_Number, Origin, Destination, Departure_Time, Arrival_Time, Aircraft_ID, Status) VALUES (%s,%s,%s,%s,%s,%s,'Scheduled')",
            (request.form['number'], request.form['origin'], request.form['destination'], request.form['depart'], request.form['arrive'], request.form['aircraft'])
        )
        conn.commit()
        flash('Flight added')
        return redirect(url_for('flights'))
    cursor.execute("SELECT * FROM Aircraft")
    aircrafts = cursor.fetchall()
    return render_template('flight_form.html', aircrafts=aircrafts)

# Bookings
@app.route('/bookings')
def bookings():
    cursor.execute("""
        SELECT b.*, p.Name AS Passenger, f.Flight_Number FROM Booking b
        JOIN Passenger p ON p.PassengerID=b.PassengerID
        JOIN Flight f ON f.FlightID=b.FlightID
    """)
    return render_template('bookings.html', bookings=cursor.fetchall())

@app.route('/booking/new', methods=['GET', 'POST'])
def booking_new():
    if request.method == 'POST':
        flight_id = request.form['flight']
        if get_available_seats(flight_id) <= 0:
            flash('No seats available on selected flight', 'error')
            return redirect(url_for('booking_new'))
        cursor.execute(
            "INSERT INTO Booking (PassengerID, FlightID, BookingDate, SeatNumber, PaymentStatus) VALUES (%s,%s,NOW(),%s,'Pending')",
            (request.form['passenger'], flight_id, request.form['seat'])
        )
        conn.commit()
        flash('Booking created')
        return redirect(url_for('bookings'))
    cursor.execute("SELECT PassengerID, Name FROM Passenger")
    passengers = cursor.fetchall()
    cursor.execute("SELECT FlightID, Flight_Number FROM Flight WHERE Status='Scheduled'")
    flights = cursor.fetchall()
    return render_template('booking_form.html', passengers=passengers, flights=flights)

# Payment
@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO Payment (BookingID, Amount, PaymentDate, PaymentMethod) VALUES (%s,%s,NOW(),%s)",
            (booking_id, request.form['amount'], request.form['method'])
        )
        cursor.execute("UPDATE Booking SET PaymentStatus='Paid' WHERE BookingID=%s", (booking_id,))
        conn.commit()
        flash('Payment recorded')
        return redirect(url_for('bookings'))
    return render_template('payment_form.html', booking_id=booking_id)

# Staff
@app.route('/staff')
def staff():
    cursor.execute("SELECT * FROM Staff")
    return render_template('staff.html', staff=cursor.fetchall())

@app.route('/staff/add', methods=['GET', 'POST'])
def staff_add():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO Staff (Name, Role, Phone, Email) VALUES (%s,%s,%s,%s)",
            (request.form['name'], request.form['role'], request.form['phone'], request.form['email'])
        )
        conn.commit()
        flash('Staff added')
        return redirect(url_for('staff'))
    return render_template('staff_form.html')

# Crew assignment
@app.route('/crew/assign', methods=['GET', 'POST'])
def crew_assign():
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO Flight_Crew (FlightID, StaffID) VALUES (%s,%s)",
            (request.form['flight'], request.form['staff'])
        )
        conn.commit()
        flash('Crew assigned')
        return redirect(url_for('crew_assign'))
    cursor.execute("SELECT FlightID, Flight_Number FROM Flight WHERE Status='Scheduled'")
    flights = cursor.fetchall()
    cursor.execute("SELECT StaffID, Name FROM Staff")
    staff = cursor.fetchall()
    return render_template('crew_form.html', flights=flights, staff=staff)

# Check-in
@app.route('/checkin/<int:booking_id>', methods=['GET', 'POST'])
def checkin(booking_id):
    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO CheckIn (BookingID, CheckInTime, BaggageCount, Gate) VALUES (%s,NOW(),%s,%s)",
            (booking_id, request.form['bags'], request.form['gate'])
        )
        conn.commit()
        flash('Passenger checked in')
        return redirect(url_for('bookings'))
    return render_template('checkin_form.html', booking_id=booking_id)

# Flight status
@app.route('/status')
def status():
    cursor.execute("SELECT Flight_Number, Status, Departure_Time, Arrival_Time FROM Flight")
    return render_template('status.html', flights=cursor.fetchall())

if __name__ == '__main__':
    app.run(debug=True)
