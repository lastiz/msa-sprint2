BEGIN;
DELETE FROM booking WHERE user_id LIKE 't2-reg-user-%';
DELETE FROM review WHERE id LIKE 't2-reg-review-%';
DELETE FROM promo_code WHERE code LIKE 'T2REGCODE%';
DELETE FROM hotel WHERE id LIKE 't2-reg-hotel-%';
DELETE FROM app_user WHERE id LIKE 't2-reg-user-%';
INSERT INTO app_user (id, status, blacklisted, active, name, email, city)
VALUES
('t2-reg-user-1', 'ACTIVE', true, true, 'Alice', 'alice@test.com', 'Seoul'),
('t2-reg-user-2', 'ACTIVE', false, true, 'Bob', 'bob@test.com', 'Busan'),
('t2-reg-user-3', 'VIP', false, true, 'Clara', 'clara@test.com', 'Daegu'),
('t2-reg-user-0', 'ACTIVE', false, false, 'Zoe', 'zoe@test.com', 'Jeju');

-- Отели
INSERT INTO hotel (id, operational, fully_booked, city, rating, description) VALUES
  ('t2-reg-hotel-1', true, false, 'Seoul', 4.7, 'Modern hotel in Seoul downtown with spa and skybar.'),
  ('t2-reg-hotel-2', true, true, 'Busan', 4.5, 'Luxury beach resort in Busan with ocean view.'),
  ('t2-reg-hotel-3', false, false, 'Daegu', 3.8, 'Affordable business hotel in Daegu center.');
  
-- Отзывы (Review)
INSERT INTO review (id, user_id, hotel_id, text, rating, created_at) VALUES
  ('t2-reg-review-001', 't2-reg-user-1', 't2-reg-hotel-1', 'Amazing experience!', 5, '2024-01-01'),
  ('t2-reg-review-002', 't2-reg-user-1', 't2-reg-hotel-1', 'Loved it!', 4, '2024-01-03'),
  ('t2-reg-review-003', 't2-reg-user-1', 't2-reg-hotel-1', 'Very good stay', 5, '2024-01-07'),
  ('t2-reg-review-004', 't2-reg-user-2', 't2-reg-hotel-1', 'Comfortable and clean', 4, '2024-01-10'),
  ('t2-reg-review-005', 't2-reg-user-2', 't2-reg-hotel-1', 'Great service', 4, '2024-01-12'),
  ('t2-reg-review-006', 't2-reg-user-2', 't2-reg-hotel-1', 'Modern rooms', 4, '2024-01-14'),
  ('t2-reg-review-007', 't2-reg-user-2', 't2-reg-hotel-1', 'Nice ambiance', 4, '2024-01-16'),
  ('t2-reg-review-008', 't2-reg-user-3', 't2-reg-hotel-1', 'Cozy and quiet', 4, '2024-01-18'),
  ('t2-reg-review-009', 't2-reg-user-3', 't2-reg-hotel-1', 'Perfect location', 4, '2024-01-20'),
  ('t2-reg-review-010', 't2-reg-user-3', 't2-reg-hotel-1', 'Will come again', 4, '2024-01-22'),

  -- Прочие отели
  ('t2-reg-review-011', 't2-reg-user-1', 't2-reg-hotel-2', 'Nice but noisy', 3, '2024-02-01'),
  ('t2-reg-review-012', 't2-reg-user-1', 't2-reg-hotel-3', 'Could be cleaner', 2, '2024-03-10');

-- Промокоды (для тестов PromoCodeController)
INSERT INTO promo_code (code, discount, vip_only, expired, valid_until, description)
VALUES
  ('T2REGCODE1', 10.0, false, false, '2099-12-31', 'Обычный промокод'),
  ('T2REGCODE-VIP', 20.0, true, false, '2099-12-31', 'Только для VIP'),
  ('T2REGCODE-OLD', 5.0, false, true, '2000-01-01', 'Истёкший промокод');
  
  
-- Бронирования (для GET /api/bookings)
INSERT INTO booking (user_id, hotel_id, promo_code, discount_percent, price, created_at)
VALUES
('t2-reg-user-2', 't2-reg-hotel-1', 'T2REGCODE1', 10.0, 90.0, NOW()),
('t2-reg-user-3', 't2-reg-hotel-1', null, 0.0, 80.0, NOW());


INSERT INTO review (id, user_id, hotel_id, text, rating, created_at)
SELECT 't2-reg-review-full-' || n, 't2-reg-user-2', 't2-reg-hotel-2', 'Trusted full hotel', 5, NOW()
FROM generate_series(1, 10) AS n;
INSERT INTO hotel (id, operational, fully_booked, city, rating, description)
VALUES ('t2-reg-hotel-4', true, false, 'Daegu', 2, 'Operational, untrusted hotel');
COMMIT;
