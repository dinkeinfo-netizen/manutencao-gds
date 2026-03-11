FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

COPY . .

ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=development
ENV TZ=America/Sao_Paulo

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
