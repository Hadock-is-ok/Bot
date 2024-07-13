FROM python:bullseye

WORKDIR /main

COPY requirements.txt .

RUN pip install -Ur requirements.txt

COPY . .
 
CMD ["python", "main.py"]