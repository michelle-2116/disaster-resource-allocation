DATA_BACKEND_DIR := DataIngestion-Allocation/backend
DATA_FRONTEND_DIR := DataIngestion-Allocation/frontend
ROUTE_BACKEND_DIR := Route-Optimizer/backend
ROUTE_FRONTEND_DIR := Route-Optimizer/frontend

.PHONY: data-backend data-frontend route-backend route-frontend status

data-backend:
	cd $(DATA_BACKEND_DIR) && venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8000

data-frontend:
	cd $(DATA_FRONTEND_DIR) && npm run dev

route-backend:
	cd $(ROUTE_BACKEND_DIR) && venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001

route-frontend:
	cd $(ROUTE_FRONTEND_DIR) && npm run dev

status:
	@printf "DataIngestion backend: "
	@curl -fsS http://127.0.0.1:8000/health >/dev/null && echo "up" || echo "down"
	@printf "Route Optimizer backend: "
	@curl -fsS http://127.0.0.1:8001/health >/dev/null && echo "up" || echo "down"
