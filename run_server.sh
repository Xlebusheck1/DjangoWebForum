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
echo "   Redis: $(redis-cli ping 2>/dev/null || echo 'FAILED')"

echo "3. Запуск Centrifugo..."

# Запускаем в фоне с логированием
nohup centrifugo -c "$PROJECT_DIR/conf/centrifugo.json" > "$PROJECT_DIR/centrifugo.log" 2>&1 &
sleep 3

# Проверяем запуск
echo "   Проверка порта 8035..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8035; then
    echo "   Centrifugo: OK (порт 8035)"
else
    echo "   Centrifugo: FAILED - смотрите centrifugo.log"
    tail -20 centrifugo.log
fi

echo "4. Запуск Django через gunicorn..."
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate --noinput

gunicorn project.wsgi:application \
    --bind 0.0.0.0:8030 \
    --workers 1 \
    --access-logfile "$PROJECT_DIR/gunicorn_access.log" \
    --error-logfile "$PROJECT_DIR/gunicorn_error.log" \
    --daemon
sleep 3

echo "   Проверка порта 8030..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8030; then
    echo "   Django/Gunicorn: OK (порт 8030)"
else
    echo "   Django/Gunicorn: FAILED"
    tail -20 gunicorn_error.log
fi

echo "5. Запуск Nginx..."
sudo nginx -c "$PROJECT_DIR/conf/nginx.local.conf"
sleep 2

echo "   Проверка порта 80..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1; then
    echo "   Nginx: OK (порт 80)"
else
    echo "   Nginx: FAILED"
fi

echo ""
echo "=== Сервисы запущены ==="
echo "Сайт: http://devguru.local"
echo "Centrifugo Admin: http://127.0.0.1:8036"
echo ""
echo "Для просмотра логов:"
echo "  tail -f centrifugo.log"
echo "  tail -f gunicorn_error.log"
echo ""
echo "Для остановки: ./stop_server.sh"