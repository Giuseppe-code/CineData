#!/bin/sh


echo "Waiting for Kafka Connect..."
until curl -sf "$CONNECT_URL/" >/dev/null; do
  sleep 2
done

echo "Creating connector es-sink-multi (if missing)..."
if curl -sf "$CONNECT_URL/connectors/es-sink-multi" >/dev/null; then
  echo "Already exists."
else
  curl -s -X POST "$CONNECT_URL/connectors" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "es-sink-multi",
      "config": {
        "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        "tasks.max": "1",
        "topics": "topboxoffice,reviewFilm,revisitedReview",
        "connection.url": "http://elasticsearch:9200",
        "key.ignore": "true",
        "schema.ignore": "true"
      }
    }' >/dev/null
  echo "Created."
fi

curl -s "$CONNECT_URL/connectors/es-sink-multi/status"
echo "ciaoooooooooooooooooo\n\nn\n\n\\n\n\n\n\n"
