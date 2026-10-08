BEGIN;
DELETE FROM booking WHERE user_id = 't2-reg-list-user';
INSERT INTO booking (user_id, hotel_id, promo_code, discount_percent, price, created_at)
VALUES
('t2-reg-list-user', 't2-reg-hotel-1', 'T2REGCODE1', 10, 90, NOW()),
('t2-reg-list-user', 't2-reg-hotel-1', NULL, 0, 100, NOW());
COMMIT;
