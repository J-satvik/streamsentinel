.PHONY: up down logs ps simulate

up:
	docker compose up -d
	@echo "Kafka UI  → http://localhost:8080"
	@echo "Grafana   → http://localhost:3000  (admin/admin)"
	@echo "Prometheus→ http://localhost:9090"

down:
	docker compose down

logs:
	docker compose logs -f kafka

ps:
	docker compose ps

simulate:
	python -m ingestion.log_simulator