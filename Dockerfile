FROM python:3.10

WORKDIR /backend

COPY penzi.py /backend

RUN pip install Flask flask-cors mysql-connector-python

# EXPOSE 5000

# CMD ["python3", "penzi.py"]

