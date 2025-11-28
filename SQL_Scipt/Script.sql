CREATE DATABASE WebProjectDB;
GO

USE WebProjectDB;
GO


CREATE TABLE Users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    fullname NVARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address NVARCHAR(255),
    role VARCHAR(20) DEFAULT 'customer',
    created_at DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE Venues (
    venue_id INT IDENTITY(1,1) PRIMARY KEY,
    venue_name NVARCHAR(100),
    location NVARCHAR(255),
    total_seats INT
);
GO

CREATE TABLE Concerts (
    concert_id INT IDENTITY(1,1) PRIMARY KEY,
    concert_name NVARCHAR(100),
    artist NVARCHAR(100),
    concert_date DATETIME,
    venue_id INT,
    status VARCHAR(20) DEFAULT 'open',
    image VARCHAR(255),
    FOREIGN KEY (venue_id) REFERENCES Venues(venue_id)
);
GO

CREATE TABLE Seats (
    seat_id INT IDENTITY(1,1) PRIMARY KEY,
    venue_id INT,
    zone VARCHAR(10),
    seat_number VARCHAR(10),
    price DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'available',
    FOREIGN KEY (venue_id) REFERENCES Venues(venue_id)
);
GO

CREATE TABLE Bookings (
    booking_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    concert_id INT,
    seat_id INT,
    total_price DECIMAL(10,2),
    booking_date DATETIME DEFAULT GETDATE(),
    booking_status VARCHAR(20) DEFAULT 'active',
    payment_status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (concert_id) REFERENCES Concerts(concert_id),
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id)
);
GO

CREATE TABLE Payments (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT,
    amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    payment_date DATETIME DEFAULT GETDATE(),
    cancel_date DATETIME,
    FOREIGN KEY (booking_id) REFERENCES Bookings(booking_id)
);
GO

INSERT INTO Users (username, password, fullname, email, role)
VALUES 
('admin', '1234', 'Administrator', 'admin@concert.com', 'admin'),
('test', '1234', 'TestUser', 'test@concert.com', 'customer');

INSERT INTO Venues (venue_name, location, total_seats)
VALUES 
(N'Impact Arena', N'Bangkok', 200),
(N'Central Hall', N'Chiang Mai', 150);

INSERT INTO Concerts (concert_name, artist, concert_date, venue_id, status, image)
VALUES 
(N'Bodyslam Live', 'Bodyslam', '2025-10-10 19:00', 1, 'open', 'bodyslam.jpg'),
(N'BNK48 6th Anniversary', 'BNK48', '2025-11-15 18:30', 2, 'open', 'bnk.jpg');
(N'BNK48 6th Anniversary', 'BNK48', '2025-11-15 18:30', 2, 'open', 'bnk.jpg')

INSERT INTO Seats (venue_id, zone, seat_number, price)
VALUES 
(1, 'VIP', 'A1', 200.00)
GO


