#!/bin/bash

set -e

echo "▶️ Testing fallback route..."

success=0
errors=0

for i in {1..10}
do
    if headers=$(curl -fsS --max-time 10 -D - -o /dev/null \
        -H "X-Fallback-Route: true" http://localhost:9090/ping); then
        status=$(printf '%s\n' "$headers" | awk '/^HTTP\// { code = $2 } END { print code }')
        version=$(printf '%s\n' "$headers" | awk '
            tolower($1) == "x-booking-version:" { gsub(/\r/, "", $2); print $2 }
        ')

        if [[ "$status" == 2[0-9][0-9] && "$version" == "v2" ]]; then
            success=$((success + 1))
        else
            echo "❌ Запрос $i: HTTP ${status:-отсутствует}, версия ${version:-отсутствует}; ожидались HTTP 2xx и v2"
            errors=$((errors + 1))
        fi
    else
        echo "❌ Запрос $i: ошибка HTTP-запроса или соединения"
        errors=$((errors + 1))
    fi
done

printf 'Успешные ответы v2: %d/10\nОшибки: %d\n' "$success" "$errors"

if [ "$errors" -gt 0 ]; then
    exit 1
fi

echo "✅ Все 10 запросов обслужены v2. Результат имеет смысл при заранее остановленной v1."
