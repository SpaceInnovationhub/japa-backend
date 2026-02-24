-- 1. Create the database (run this separately if the DB doesn't exist yet)
CREATE DATABASE japa_db;

-- Connect to the new database first:
-- \c japa_db

-- 2. Users table (core table)
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    fullname        VARCHAR(100)        NOT NULL,
    passport_number VARCHAR(50) UNIQUE,
    nin             VARCHAR(50) UNIQUE,
    email           VARCHAR(100) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    password        TEXT                NOT NULL,   -- should be hashed!
    country         VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Support tickets (updated version with embassy_country + timestamp)
CREATE TABLE support_tickets (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    embassy_country VARCHAR(50),
    subject         VARCHAR(200)        NOT NULL,
    description     TEXT                NOT NULL,
    status          VARCHAR(30)         DEFAULT 'open',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Announcements (updated version with category + timestamp)
CREATE TABLE announcements (
    id              SERIAL PRIMARY KEY,
    embassy_country VARCHAR(50),
    title           VARCHAR(200)        NOT NULL,
    content         TEXT                NOT NULL,
    category        VARCHAR(20),                    -- e.g. 'visa', 'travel', 'safety', 'general'
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Evacuation requests
CREATE TABLE evacuation_requests (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id) ON DELETE CASCADE,
    country     VARCHAR(50)         NOT NULL,
    status      VARCHAR(30)         DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Incident reports (new table)
CREATE TABLE incident_reports (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    embassy_country VARCHAR(50),
    description     TEXT                NOT NULL,
    media_path      TEXT,                           -- path or URL to photo/video
    status          VARCHAR(30)         DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: useful indexes (add these after data volume grows)
CREATE INDEX idx_support_tickets_user    ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_country ON support_tickets(embassy_country);
CREATE INDEX idx_announcements_country   ON announcements(embassy_country);
CREATE INDEX idx_evacuation_user         ON evacuation_requests(user_id);
CREATE INDEX idx_incident_user           ON incident_reports(user_id);
CREATE INDEX idx_incident_country        ON incident_reports(embassy_country);