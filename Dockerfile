FROM python:2.7
ADD . .
RUN pip install -r requirements.txt
EXPOSE 5050
