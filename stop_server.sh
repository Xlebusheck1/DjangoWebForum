#!/bin/bash

PROJECT_DIR="/mnt/c/Users/Максим/programs/ForumVKWebDjango"

echo "=== Остановка всех сервисов ==="

echo "1. Остановка Nginx..."
sudo nginx -s stop 2>/dev/null || true

echo "2. Остановка Gunicorn..."
pkill -f "gunicorn" 2>/dev/null || true

echo "3. Остановка Centrifugo..."
pkill -f "centrifugo" 2>/dev/null || true

echo "4. Остановка Redis..."
redis-cli shutdown 2>/dev/null || true

echo "5. Освобождение портов..."
sudo fuser -k 80/tcp 2>/dev/null || true
sudo fuser -k 8030/tcp 2>/dev/null || true
sudo fuser -k 8035/tcp 2>/dev/null || true
sudo fuser -k 8036/tcp 2>/dev/null || true

sleep 2
echo "=== Все сервисы остановлены ==="