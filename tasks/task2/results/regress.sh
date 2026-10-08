#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
BASE="${API_URL:-http://localhost:8084}"

pass() { echo "✅ $1"; }
fail() { echo "❌ $1"; exit 1; }

sql() {
  docker compose exec -T "$1" psql -X -qAt -v ON_ERROR_STOP=1 -U hotelio -d hotelio "${@:2}"
}

echo "🏁 Регрессионный тест Hotelio после выделения booking-service"
command -v jq >/dev/null || fail "Для запуска нужен jq"

echo "🧪 Проверка подключения к базам..."
sql monolith-db -c 'SELECT 1' >/dev/null || fail "БД монолита недоступна"
sql booking-db -c 'SELECT 1' >/dev/null || fail "БД бронирований недоступна"
sql history-db -c 'SELECT 1' >/dev/null || fail "БД истории недоступна"

echo "🧪 Загрузка фикстур..."
sql monolith-db < init-fixtures.sql
sql booking-db < init-fixtures-booking.sql

echo "🧪 Выполнение HTTP-тестов..."
echo ""
echo "Тесты пользователей..."
# 1. Получение пользователя по ID
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-1" | grep -q 'Alice' && pass "Получение t2-reg-user-1 по ID работает" || fail "Пользователь t2-reg-user-1 не найден"

# 2. Статус пользователя
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-1/status" | grep -q 'ACTIVE' && pass "Статус t2-reg-user-1: ACTIVE" || fail "Неверный статус пользователя"

# 3. Блэклист
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-1/blacklisted" | grep -q 'true' && pass "t2-reg-user-1 в блэклисте" || fail "Блэклист не работает"

# 4. Активность
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-1/active" | grep -q 'true' && pass "t2-reg-user-1 активен" || fail "Активность не работает"

# 5. Авторизация
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-1/authorized" | grep -q 'false' && pass "t2-reg-user-1 не авторизован (в блэклисте)" || fail "Авторизация работает неправильно"

# 6. VIP-статус
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-3/vip" | grep -q 'true' && pass "t2-reg-user-3 — VIP-пользователь" || fail "VIP-статус не работает"

# 7. Авторизация: положительный кейс
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/users/t2-reg-user-2/authorized" | grep -q 'true' && pass "t2-reg-user-2 авторизован" || fail "Авторизация (true) не работает"

echo ""
echo "Тесты отелей..."

# 1. Получение отеля по ID
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/t2-reg-hotel-1" | grep -q 'Seoul' && pass "t2-reg-hotel-1 получен по ID" || fail "t2-reg-hotel-1 не найден"

# 2. Проверка operational
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/t2-reg-hotel-1/operational" | grep -q 'true' && pass "t2-reg-hotel-1 работает" || fail "t2-reg-hotel-1 не работает"
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/t2-reg-hotel-3/operational" | grep -q 'false' && pass "t2-reg-hotel-3 не работает" || fail "Статус работы t2-reg-hotel-3 некорректен"

# 3. Проверка fullyBooked
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/t2-reg-hotel-2/fully-booked" | grep -q 'true' && pass "t2-reg-hotel-2 полностью забронирован" || fail "Статус fullyBooked t2-reg-hotel-2 неверен"

# 4. Поиск по городу
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/by-city?city=Seoul" | grep -q 'Seoul' && pass "Поиск отелей в Сеуле работает" || fail "Поиск отелей в Сеуле не работает"

# 5. Топ-отели (по рейтингу, limit)
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/hotels/top-rated?city=Seoul&limit=1" | grep -q 'Seoul' && pass "Топ-отели в Сеуле загружены" || fail "Топ-отели не найдены"

echo ""
echo "Тесты ревью..."

# 11. Отзывы по hotelId
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/reviews/hotel/t2-reg-hotel-1" | grep -q 'Amazing experience' \
  && pass "Отзывы t2-reg-hotel-1 найдены" || fail "Отзывы t2-reg-hotel-1 не найдены"

# 12. Надёжный отель (>=10 отзывов и avgRating >= 4.0)
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/reviews/hotel/t2-reg-hotel-1/trusted" | grep -q 'true' \
  && pass "t2-reg-hotel-1 признан надёжным" || fail "Надёжность t2-reg-hotel-1 не определена"

# 13. Сомнительный отель (мало отзывов/низкий рейтинг)
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/reviews/hotel/t2-reg-hotel-3/trusted" | grep -q 'false' \
  && pass "t2-reg-hotel-3 НЕ признан надёжным (ожидаемо)" || fail "Надёжность t2-reg-hotel-3 некорректно определена"

echo ""
echo "Тесты промокодов..."

# 1. Получение промо по коду
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/promos/T2REGCODE1" | grep -q 'T2REGCODE1' && pass "Промокод T2REGCODE1 найден" || fail "Промокод T2REGCODE1 не найден"

# 2. Проверка VIP промо — для VIP
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/promos/T2REGCODE-VIP/valid?isVipUser=true" | grep -q 'true' && pass "VIP-промо доступен VIP" || fail "VIP-промо НЕ доступен VIP"

# 3. Проверка VIP промо — для обычного
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/promos/T2REGCODE-VIP/valid?isVipUser=false" | grep -q 'false' && pass "VIP-промо недоступен обычному" || fail "VIP-промо доступен обычному"

# 4. Проверка обычного промо
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/promos/T2REGCODE1/valid" | grep -q 'true' && pass "Обычный промо доступен" || fail "Обычный промо недоступен"

# 5. Проверка истекшего промо
curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/promos/T2REGCODE-OLD/valid" | grep -q 'false' && pass "Истекший промо недоступен" || fail "Истекший промо доступен"

# 6. Валидация промо для user-2 (обычного)
curl --connect-timeout 5 --max-time 15 -sSf -X POST "${BASE}/api/promos/validate?code=T2REGCODE1&userId=t2-reg-user-2" | grep -q 'T2REGCODE1' && pass "POST /validate промо прошёл" || fail "POST /validate не прошёл"

echo ""
echo "Тесты бронирования..."

curl --connect-timeout 5 --max-time 15 -sSf "${BASE}/api/bookings?userId=t2-reg-list-user" \
  | grep -q 't2-reg-list-user' \
  && pass "Бронирования пользователя получены через REST" || fail "REST-список бронирований недоступен"

booking=$(curl --connect-timeout 5 --max-time 15 -sSf -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-3&hotelId=t2-reg-hotel-1")
echo "$booking" | jq -e '.hotelId == "t2-reg-hotel-1" and .price == 80' >/dev/null \
  && pass "Бронирование без промо прошло" || fail "Неверное бронирование без промо"
booking_id=$(echo "$booking" | jq -r '.id')

booking=$(curl --connect-timeout 5 --max-time 15 -sSf -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-2&hotelId=t2-reg-hotel-1&promoCode=T2REGCODE1")
echo "$booking" | jq -e '.promoCode == "T2REGCODE1" and .price == 90' >/dev/null \
  && pass "Бронирование с промо прошло" || fail "Неверное бронирование с промо"
promo_booking_id=$(echo "$booking" | jq -r '.id')
[[ "$booking_id" =~ ^[0-9]+$ && "$promo_booking_id" =~ ^[0-9]+$ ]] \
  || fail "Некорректные идентификаторы бронирований"

code=$(curl --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-0&hotelId=t2-reg-hotel-1")
[[ "$code" == 500 ]] && pass "Отклонён неактивный пользователь" || fail "Неактивный пользователь: HTTP $code"

code=$(curl --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-1&hotelId=t2-reg-hotel-1")
[[ "$code" == 500 ]] && pass "Отклонён пользователь в блэклисте" || fail "Блэклист: HTTP $code"

code=$(curl --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-2&hotelId=t2-reg-hotel-3")
[[ "$code" == 500 ]] && pass "Отклонён закрытый отель" || fail "Закрытый отель: HTTP $code"

code=$(curl --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-2&hotelId=t2-reg-hotel-4")
[[ "$code" == 500 ]] && pass "Отклонён недоверенный отель" || fail "Недоверенный отель: HTTP $code"

code=$(curl --connect-timeout 5 --max-time 15 -sS -o /dev/null -w '%{http_code}' -X POST \
  "${BASE}/api/bookings?userId=t2-reg-user-2&hotelId=t2-reg-hotel-2")
[[ "$code" == 500 ]] && pass "Отклонён полностью занятый отель" || fail "Занятый отель: HTTP $code"

echo ""
echo "🧪 Проверка списка через gRPC..."
docker compose run --rm --no-deps -T grpcurl -plaintext -max-time 10 \
  -import-path /proto -proto booking.proto -d '{"userId":"t2-reg-user-2"}' \
  booking-service:9090 booking.BookingService/ListBookings \
  | jq -e --arg id "$promo_booking_id" '.bookings | any(.[]; (.id | tostring) == $id)' >/dev/null \
  && pass "Созданное бронирование найдено через gRPC" || fail "Бронирование не найдено через gRPC"

echo ""
echo "🧪 Ожидание истории двух новых бронирований (до 10 секунд)..."
for attempt in {1..10}; do
  count=$(sql history-db -c "SELECT count(DISTINCT booking_id) FROM booking_history WHERE booking_id IN ('$booking_id', '$promo_booking_id');")
  if [[ "$count" == 2 ]]; then
    pass "История обоих новых бронирований получена"
    echo "✅ Все тесты пройдены!"
    exit 0
  fi
  sleep 1
done
fail "История новых бронирований не появилась за 30 секунд"
