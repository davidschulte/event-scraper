FROM python:latest
WORKDIR /code
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY main.py main.py
COPY db_utils.py db_utils.py
CMD ["python", "-u", "main.py"]
