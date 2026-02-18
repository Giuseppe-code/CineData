#!/bin/bash

echo "🚀 AVVIO PIPELINE CINEDATA"
echo "=========================="

# 1. Kafka
echo "1️⃣  Avvio Kafka..."
docker compose --profile kafka --profile kafka-topic up -d
echo "   Attendo 20s per inizializzazione Kafka..."
sleep 20

# 2. Visual stack
echo "2️⃣  Avvio Elasticsearch + Kibana + Kafka Connect..."
docker compose --profile clk up -d
echo "   Attendo 3min per installazione plugin Kafka Connect..."
sleep 120

# 4. Spark
echo "3️⃣  Avvio Spark..."
docker compose --profile sparkText --profile clk up -d
echo "   Attendo 30s per avvio Spark..."
sleep 30

# 5. Verifica
echo ""
echo "✅ Verifica stato:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "kafka|spark|elastic|kibana|fluent"

echo ""
echo "=========================="
echo "✅ Pipeline avviata!"
echo ""
echo "📊 Kibana:    http://localhost:5601"
echo "🔧 Connect:   http://localhost:8083"
echo "🔍 ES:        http://localhost:9200"
echo ""
echo "Per avviare scraping (title a tua scelta):"
echo "  docker compose run --rm scraping python main_scraper.py --demo tt0133093  --title "The Matrix" --max-reviews 20"