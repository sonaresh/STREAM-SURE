FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir . -r requirements-kafka.txt
USER 10001:10001
CMD ["python","-m","streamsure.adapters.kafka_bridge"]
