# python image base
FROM python:3.11-slim

# set workdir in container
WORKDIR /app

# copy requirements
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy code
COPY . .

# flask port
EXPOSE 5000

# env variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# start flask
CMD ["flask", "run"]
