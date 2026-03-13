FROM python:3.12-slim
EXPOSE 5000
WORKDIR /app

# Install dos2unix to ensure that the entrypoint file starts as expected
RUN apt update
RUN apt install -y dos2unix

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY scripts/app/entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]