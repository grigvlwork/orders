FROM python AS builder
COPY requirements.txt .

RUN pip install --user -r requirements.txt

FROM python:3.10-slim-buster
WORKDIR /code
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local:$PATH
CMD ["python", "-u", "./main.py"]
