-- MedSpa API schema
-- Run with: psql -U postgres -d medspa_db -f schema.sql (from /sql in container)

-- Medspas: basic info
CREATE TABLE IF NOT EXISTS medspas (
    id CHAR(26) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone_number VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Services: catalog per medspa
CREATE TABLE IF NOT EXISTS services (
    id CHAR(26) PRIMARY KEY,
    medspa_id CHAR(26) NOT NULL REFERENCES medspas(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL CHECK (price > 0),
    -- price in cents per spec
    duration INTEGER NOT NULL CHECK (duration > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_services_medspa_id ON services(medspa_id);

-- Appointments: bookings (total_price and total_duration stored for historical accuracy)
CREATE TABLE IF NOT EXISTS appointments (
    id CHAR(26) PRIMARY KEY,
    medspa_id CHAR(26) NOT NULL REFERENCES medspas(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('scheduled', 'completed', 'canceled')),
    total_price INTEGER NOT NULL,
    -- total_price in cents (derived from services at creation)
    total_duration INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_appointments_medspa_id ON appointments(medspa_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments(start_time);

-- Appointment-Services: many-to-many (service_id ON DELETE RESTRICT to preserve history)
CREATE TABLE IF NOT EXISTS appointment_services (
    appointment_id CHAR(26) NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    service_id CHAR(26) NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
    PRIMARY KEY (appointment_id, service_id)
);
CREATE INDEX IF NOT EXISTS idx_appointment_services_appointment_id ON appointment_services(appointment_id);
CREATE INDEX IF NOT EXISTS idx_appointment_services_service_id ON appointment_services(service_id);
