FROM tiangolo/uwsgi-nginx:python3.6

ENV PYTHONUNBUFFERED 1

RUN rm -rf /app/*

RUN apt-get update && apt-get install -y --no-install-recommends \
	ca-certificates \
	git \
	make \
	openscad \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /root/.local/share /.local/share

WORKDIR /app


COPY . .
RUN pip install -r requirements.txt


EXPOSE $PORT

ARG secret_key
ENV SECRET_KEY=${secret_key}
RUN python manage.py collectstatic --no-input

CMD gunicorn --bind 0.0.0.0:$PORT --workers 3 backend.wsgi:application