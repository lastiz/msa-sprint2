#!/bin/bash

set -e

echo "▶️ Checking canary release (90% v1, 10% v2)..."

v1=0
v2=0
errors=0

# Посылаем 100 запросов
for i in {1..100}
do
    if headers=$(curl -fsS --max-time 10 -D - -o /dev/null http://localhost:9090/ping); then
        version=$(printf '%s\n' "$headers" | awk '
            tolower($1) == "x-booking-version:" { gsub(/\r/, "", $2); print $2 }
        ')
        case "$version" in
            v1) v1=$((v1 + 1)) ;;
            v2) v2=$((v2 + 1)) ;;
            *) errors=$((errors + 1)) ;;
        esac
    else
        errors=$((errors + 1))
    fi
done

# Из 100 запросов количество ответов совпадает с процентом.
printf 'v1: %d (%d%%)\nv2: %d (%d%%)\nErrors: %d\n' "$v1" "$v1" "$v2" "$v2" "$errors"
echo "Ожидается примерно 90% v1 / 10% v2, а не точное совпадение."

if [ "$errors" -gt 0 ]; then
    exit 1
fi
