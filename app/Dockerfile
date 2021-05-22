FROM python:3.8-buster
COPY . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD ["gunicorn", "--workers=2", "-b", ":3800", "--timeout=500", "app:server"]