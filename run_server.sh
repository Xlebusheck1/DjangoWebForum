#!/bin/bash

PROJECT_DIR="/mnt/c/Users/Максим/programs/ForumVKWebDjango"
cd "$PROJECT_DIR"

echo "=== Запуск всех сервисов ==="

echo "1. Остановка старых сервисов..."
pkill -f "centrifugo" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
sudo nginx -s stop 2>/dev/null || true
redis-cli shutdown 2>/dev/null || true
sleep 2

echo "2. Запуск Redis..."
redis-server --daemonize yes
sleep 2
echo "   Redis запущен"

echo "3. Запуск Centrifugo..."
centrifugo -c "$PROJECT_DIR/conf/centrifugo.json" > centrifugo.log 2>&1 &
sleep 3
echo "   Centrifugo запущен на порту 8035"
echo "   Логи: tail -f centrifugo.log"

echo "4. Запуск Django..."
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate --noinput

gunicorn project.wsgi:application \
    --bind 0.0.0.0:8030 \
    --workers 3 \
    --access-logfile gunicorn_access.log \
    --error-logfile gunicorn_error.log \
    --daemon
sleep 3
echo "   Django запущен на порту 8030"

echo "5. Запуск Nginx..."
sudo nginx -c "$PROJECT_DIR/conf/nginx.local.conf"
sleep 2
echo "   Nginx запущен"

echo ""
echo "=== ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ ==="
echo ""
