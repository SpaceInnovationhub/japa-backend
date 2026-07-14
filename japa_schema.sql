-- 1. Setup
CREATE DATABASE japa_db;
-- \c japa_db

-- 2. Users (Added: role, is_active)
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    fullname        VARCHAR(100)        NOT NULL,
    passport_number VARCHAR(50) UNIQUE,
    nin             VARCHAR(50) UNIQUE,
    email           VARCHAR(100) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    password        TEXT                NOT NULL, -- Hashed Bcrypt string
    country         VARCHAR(50),        -- User's origin/residence
    role            VARCHAR(20)         DEFAULT 'user', -- 'user', 'admin', 'embassy'
    is_active       BOOLEAN             DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Support Tickets (Added: priority)
CREATE TABLE support_tickets (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    embassy_country VARCHAR(50),
    subject         VARCHAR(200)        NOT NULL,
    description     TEXT                NOT NULL,
    status          VARCHAR(30)         DEFAULT 'open', -- 'open', 'in-progress', 'closed'
    priority        VARCHAR(10)         DEFAULT 'medium',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Announcements
CREATE TABLE announcements (
    id              SERIAL PRIMARY KEY,
    author_id       INT REFERENCES users(id), -- Tracks which admin posted it
    embassy_country VARCHAR(50),
    title           VARCHAR(200)        NOT NULL,
    content         TEXT                NOT NULL,
    category        VARCHAR(20),        -- 'visa', 'travel', 'safety', 'general'
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Incident Reports (Added: coordinates for GPS)
CREATE TABLE incident_reports (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    embassy_country VARCHAR(50),
    description     TEXT                NOT NULL,
    media_path      TEXT,               -- Path to file saved via your FileService
    location_coords VARCHAR(100),       -- "Lat, Long"
    status          VARCHAR(30)         DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Evacuation Requests
CREATE TABLE evacuation_requests (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id) ON DELETE CASCADE,
    country     VARCHAR(50)         NOT NULL,
    status      VARCHAR(30)         DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Speed
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_announcements_country ON announcements(embassy_country);