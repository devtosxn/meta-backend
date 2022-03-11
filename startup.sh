
python manage.py collectstatic --no-input

gunicorn --bind 0.0.0.0:$PORT --workers 3 backend.wsgi:application