from flask import Flask, render_template, request, redirect, session
import pyodbc
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concert_secret'

# Connection
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=NATTHAPHUMIN;'
    'DATABASE=WebProjectDB;'
    'Trusted_Connection=yes;'
    'Encrypt=no;'
)

# Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = user[1]
            session['fullname'] = user[3]
            return redirect('/home')
        else:
            return render_template('login.html', error='ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render_template('login.html')

#register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', error='ชื่อผู้ใช้นี้ถูกใช้แล้ว')

        cursor.execute("""
            INSERT INTO Users (username, password, fullname, email, role)
            VALUES (?, ?, ?, ?, 'customer')
        """, (username, password, fullname, email))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template('register.html')

@app.route('/about')
def about():
    if 'fullname' not in session:
        return render_template('about.html')
    return render_template('about.html')

@app.route('/home')
def home(): 
    user = session.get('fullname', None)
    return render_template('home.html', user=user)

@app.route('/account')
def account():
    if 'fullname' in session:
        return render_template('account.html')
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ===== Venue Management =====
@app.route('/venue')
def venue():
    if 'fullname' not in session:
        return redirect('/')

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT venue_id, venue_name, location, total_seats FROM Venues")
    venues = cursor.fetchall()
    conn.close()
    return render_template('venue.html', venues=venues)


@app.route('/add_venue', methods=['POST'])
def add_venue():
    name = request.form['venue_name']
    loc = request.form['location']
    total = request.form['total_seats']

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Venues (venue_name, location, total_seats) VALUES (?, ?, ?)",
        (name, loc, total)
    )
    conn.commit()
    conn.close()
    return redirect('/venue')


@app.route('/edit_venue/<int:venue_id>')
def edit_venue(venue_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT venue_id, venue_name, location, total_seats FROM Venues WHERE venue_id = ?", (venue_id,))
    venue = cursor.fetchone()
    conn.close()
    return render_template('edit_venue.html', venue=venue)


@app.route('/update_venue/<int:venue_id>', methods=['POST'])
def update_venue(venue_id):
    name = request.form['venue_name']
    loc = request.form['location']
    total = request.form['total_seats']

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Venues SET venue_name=?, location=?, total_seats=? WHERE venue_id=?",
        (name, loc, total, venue_id)
    )
    conn.commit()
    conn.close()
    return redirect('/venue')


@app.route('/delete_venue/<int:venue_id>')
def delete_venue(venue_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Venues WHERE venue_id = ?", (venue_id,))
    conn.commit()
    conn.close()
    return redirect('/venue')

#concert management
# ตั้งค่าโฟลเดอร์อัปโหลดภาพ
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# สร้างโฟลเดอร์ถ้ายังไม่มี
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ฟังก์ชันตรวจสอบนามสกุลไฟล์
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/concert_management')
def concert_management():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.concert_id, c.concert_name, c.artist, c.concert_date, 
               c.image_path, v.venue_name, c.status
        FROM Concerts c
        LEFT JOIN Venues v ON c.venue_id = v.venue_id
    """)
    concerts = cursor.fetchall()
    conn.close()
    return render_template('concert_management.html', concerts=concerts)


@app.route('/add_concert', methods=['GET', 'POST'])
def add_concert():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT venue_id, venue_name FROM Venues")
    venues = cursor.fetchall()

    if request.method == 'POST':
        concert_name = request.form['concert_name']
        artist = request.form['artist']
        concert_date = request.form['concert_date']
        venue_id = request.form['venue_id']
        status = request.form['status']
        image = request.files['concert_image']

        # แปลงค่า datetime-local เป็นรูปแบบที่ SQL Server เข้าใจ
        concert_date = concert_date.replace("T", " ") + ":00"

        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute("""
            INSERT INTO Concerts (concert_name, artist, concert_date, venue_id, image_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (concert_name, artist, concert_date, venue_id, filename, status))
        conn.commit()
        conn.close()
        return redirect('/concert_management')

    conn.close()
    return render_template('add_concert.html', venues=venues)


@app.route('/edit_concert/<int:concert_id>', methods=['GET', 'POST'])
def edit_concert(concert_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("SELECT venue_id, venue_name FROM Venues")
    venues = cursor.fetchall()

    cursor.execute("SELECT * FROM Concerts WHERE concert_id = ?", (concert_id,))
    concert = cursor.fetchone()

    if request.method == 'POST':
        concert_name = request.form['concert_name']
        artist = request.form['artist']
        concert_date = request.form['concert_date']
        venue_id = request.form['venue_id']
        status = request.form['status']
        image = request.files['concert_image']

        concert_date = concert_date.replace("T", " ") + ":00"

        # ตรวจว่ามีการอัปโหลดภาพใหม่ไหม
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("""
                UPDATE Concerts 
                SET concert_name=?, artist=?, concert_date=?, venue_id=?, image_path=?, status=? 
                WHERE concert_id=?
            """, (concert_name, artist, concert_date, venue_id, filename, status, concert_id))
        else:
            cursor.execute("""
                UPDATE Concerts 
                SET concert_name=?, artist=?, concert_date=?, venue_id=?, status=? 
                WHERE concert_id=?
            """, (concert_name, artist, concert_date, venue_id, status, concert_id))

        conn.commit()
        conn.close()
        return redirect('/concert_management')

    conn.close()
    return render_template('edit_concert.html', concert=concert, venues=venues)

# Delete Concert
@app.route('/delete_concert/<int:concert_id>')
def delete_concert(concert_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Concerts WHERE concert_id=?", (concert_id,))
    conn.commit()
    conn.close()
    return redirect('/concert_management')

@app.route('/concerts')
def view_concerts():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.concert_id, c.concert_name, c.artist, c.concert_date, 
               c.image_path, v.venue_name, c.status
        FROM Concerts c
        LEFT JOIN Venues v ON c.venue_id = v.venue_id
        ORDER BY c.concert_date ASC
    """)
    concerts = cursor.fetchall()
    conn.close()
    return render_template('concert_list.html', concerts=concerts)

##seat pricing
@app.route('/seat_pricing')
def seat_pricing():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT zone, 
               ISNULL(AVG(price), 0) AS avg_price 
        FROM Seats 
        GROUP BY zone
        ORDER BY 
            CASE 
                WHEN zone='VIP' THEN 1 
                WHEN zone='A' THEN 2 
                WHEN zone='B' THEN 3 
                WHEN zone='C' THEN 4 
                ELSE 5 END
    """)
    seat_prices = cursor.fetchall()
    conn.close()
    return render_template('seat_pricing.html', seat_prices=seat_prices)


@app.route('/save_seat_pricing', methods=['POST'])
def save_seat_pricing():
    vip = request.form.get('vip_price', 0)
    a = request.form.get('a_price', 0)
    b = request.form.get('b_price', 0)
    c = request.form.get('c_price', 0)

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("UPDATE Seats SET price = ? WHERE zone = 'VIP'", (vip,))
    cursor.execute("UPDATE Seats SET price = ? WHERE zone = 'A'", (a,))
    cursor.execute("UPDATE Seats SET price = ? WHERE zone = 'B'", (b,))
    cursor.execute("UPDATE Seats SET price = ? WHERE zone = 'C'", (c,))
    conn.commit()
    conn.close()

    return redirect('/seat_pricing')


#concert list
@app.route('/concert/<int:concert_id>/seats')
def select_seats(concert_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # ดึงข้อมูล concert + ที่นั่งทั้งหมดของ venue นั้น
    cursor.execute("""
        SELECT c.concert_id, c.concert_name, c.artist, v.venue_name, v.venue_id
        FROM Concerts c
        JOIN Venues v ON c.venue_id = v.venue_id
        WHERE c.concert_id = ?
    """, (concert_id,))
    concert = cursor.fetchone()

    cursor.execute("""
        SELECT seat_id, seat_number, zone, price, status
        FROM Seats
        WHERE venue_id = ?
        ORDER BY zone, seat_number
    """, (concert.venue_id,))
    seats = cursor.fetchall()

    conn.close()

    return render_template('select_seat.html', concert=concert, seats=seats)

# -----------------------------------------------------
# หน้าเลือกที่นั่ง
# -----------------------------------------------------
@app.route('/select_seat/<int:concert_id>')
def seat_selection(concert_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # ✅ ดึงข้อมูลคอนเสิร์ต + สถานที่
    cursor.execute("""
        SELECT c.concert_id, c.concert_name, c.artist, c.venue_id, v.venue_name
        FROM Concerts c
        JOIN Venues v ON c.venue_id = v.venue_id
        WHERE c.concert_id = ?
    """, (concert_id,))
    concert = cursor.fetchone()

    if not concert:
        conn.close()
        return "ไม่พบข้อมูลคอนเสิร์ต", 404

    # ✅ ดึงข้อมูลที่นั่งของสถานที่นั้น
    cursor.execute("""
        SELECT seat_id, zone, seat_number, price
        FROM Seats
        WHERE venue_id = ?
        ORDER BY zone, seat_number
    """, (concert.venue_id,))
    seats = cursor.fetchall()

    conn.close()
    return render_template('select_seat.html', concert=concert, seats=seats)


# -----------------------------------------------------
# Checkout + ชำระเงิน (INSERT Bookings & Payments)
# -----------------------------------------------------
@app.route('/checkout', methods=['POST'])
def checkout():
    seat_id = request.form['seat_id']
    concert_id = request.form['concert_id']

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # ✅ ดึงราคาที่นั่ง
    cursor.execute("SELECT price FROM Seats WHERE seat_id=?", (seat_id,))
    price = cursor.fetchone()[0]

    # ✅ สร้างข้อมูลการจอง
    user_id = session.get('user_id', 1)  # mock user
    booking_date = datetime.now()

    cursor.execute("""
    INSERT INTO Bookings (user_id, concert_id, seat_id, total_price, booking_date, booking_status, payment_status)
    OUTPUT INSERTED.booking_id
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, concert_id, seat_id, price, booking_date, 'Confirmed', 'Paid'))

    booking_id = cursor.fetchone()[0]


    # ✅ สร้างข้อมูลการชำระเงิน
    cursor.execute("""
        INSERT INTO Payments (booking_id, payment_date, amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?)
    """, (booking_id, booking_date, price, 'Credit Card', 'Success'))

    conn.commit()
    conn.close()

    return render_template('payment_success.html', price=price)

##order
@app.route('/orders')
def orders():
    user_id = session.get('user_id', 1)  # mock user

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            b.booking_id,
            c.concert_name,
            c.artist,
            v.venue_name,
            s.zone,
            s.seat_number,
            b.total_price,
            b.booking_date,
            p.payment_method,
            p.status AS payment_status
        FROM Bookings b
        JOIN Concerts c ON b.concert_id = c.concert_id
        JOIN Venues v ON c.venue_id = v.venue_id
        JOIN Seats s ON b.seat_id = s.seat_id
        LEFT JOIN Payments p ON b.booking_id = p.booking_id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    """, (user_id,))

    orders = cursor.fetchall()
    conn.close()

    return render_template('orders.html', orders=orders)


@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # ✅ 1. ตรวจสอบว่าการจองนี้มีอยู่ไหม
    cursor.execute("SELECT seat_id FROM Bookings WHERE booking_id = ?", (booking_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return "ไม่พบข้อมูลการจองนี้", 404

    seat_id = result[0]

    # ✅ 2. อัปเดตสถานะในตาราง Bookings และ Payments
    cursor.execute("""
        UPDATE Bookings
        SET booking_status = 'Cancelled', payment_status = 'Refunded'
        WHERE booking_id = ?
    """, (booking_id,))

    cursor.execute("""
        UPDATE Payments
        SET status = 'Refunded'
        WHERE booking_id = ?
    """, (booking_id,))

    # ✅ 3. ปล่อยที่นั่งให้ว่างอีกครั้ง
    cursor.execute("""
        UPDATE Seats
        SET status = 'Available'
        WHERE seat_id = ?
    """, (seat_id,))

    conn.commit()
    conn.close()

    # ✅ 4. กลับไปหน้า orders อีกครั้ง
    return redirect('/orders')

    
if __name__ == '__main__':
    app.run(debug=True)


