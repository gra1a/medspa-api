-- Optional seed data for manual testing. Not used by automated tests.
-- Run after schema.sql. IDs are fixed for reproducibility.

INSERT INTO medspas (id, name, address, phone_number, email) VALUES
    ('01ARZ3NDEKTSV4RRFFQ69G5FAV', 'Serenity MedSpa', '123 Main St, Austin TX', '(512) 555-0100', 'hello@serenitymedspa.com'),
    ('01ARZ3NDEKTSV4RRFFQ69G5FB0', 'Glow Wellness', '456 Oak Ave, Austin TX', '(512) 555-0200', 'info@glowwellness.com');

-- price in cents per spec
INSERT INTO services (id, medspa_id, name, description, price, duration) VALUES
    ('01ARZ3NDEKTSV4RRFFQ69G5FB1', '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'Facial', 'Standard facial treatment', 8500, 60),
    ('01ARZ3NDEKTSV4RRFFQ69G5FB2', '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'Massage', '60-minute relaxation massage', 12000, 60),
    ('01ARZ3NDEKTSV4RRFFQ69G5FB3', '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'Botox Consultation', 'Consultation and assessment', 1, 30),
    ('01ARZ3NDEKTSV4RRFFQ69G5FB4', '01ARZ3NDEKTSV4RRFFQ69G5FAV', 'Chemical Peel', 'Light chemical peel', 15000, 45),
    ('01ARZ3NDEKTSV4RRFFQ69G5FB5', '01ARZ3NDEKTSV4RRFFQ69G5FB0', 'Laser Hair Removal', 'Single session', 20000, 30);
