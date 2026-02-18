#!/bin/sh

CONNECT_URL="${CONNECT_URL:-http://kafka-connect:8083}"

echo "Waiting for Kafka Connect to be ready..."
until curl -sf "$CONNECT_URL/connectors" > /dev/null; do
  echo "Not ready yet..."
  sleep 5
done

echo "Waiting for Elasticsearch plugin to be loaded..."
until curl -sf "$CONNECT_URL/connector-plugins" | grep -q "ElasticsearchSinkConnector"; do
  echo "Plugin not yet available..."
  sleep 5
done

echo "Plugin ready! Registering connector..."
curl -sf -X POST "$CONNECT_URL/connectors" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "es-sink-multi",
    "config": {
      "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
      "tasks.max": "1",
      "topics": "topboxoffice,reviewFilm,revisedReview",
      "connection.url": "http://elasticsearch:9200",
      "key.ignore": "true",
      "schema.ignore": "true"
    }
  }'

echo "Done!"