FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Usa lo stesso interpreter per installare
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r /app/requirements.txt 

COPY . /app

CMD ["python", "scrapingBoxOffice.py"]
