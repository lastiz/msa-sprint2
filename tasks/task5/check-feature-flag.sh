#!/bin/bash

set -e

echo "▶️ Проверка Feature Flag (X-Feature-Enabled: true)..."

# Отправляем запрос с заголовком, чтобы маршрутизировать трафик на `v2`
if ! headers=$(curl -fsS --max-time 10 -D - -o /dev/null \
    -H "X-Feature-Enabled: true" http://localhost:9090/ping); then
    echo "❌ Ошибка HTTP-запроса или соединения"
    exit 1
fi

status=$(printf '%s\n' "$headers" | awk '/^HTTP\// { code = $2 } END { print code }')
version=$(printf '%s\n' "$headers" | awk '
    tolower($1) == "x-booking-version:" { gsub(/\r/, "", $2); print $2 }
')

if [[ "$status" != 2[0-9][0-9] ]]; then
    echo "❌ Ожидался HTTP 2xx, получен: ${status:-отсутствует}"
    exit 1
fi

if [ "$version" != "v2" ]; then
    echo "❌ Ожидался X-Booking-Version: v2, получен: ${version:-отсутствует}"
    exit 1
fi

echo "✅ Feature Flag: HTTP $status, X-Booking-Version: $version"
