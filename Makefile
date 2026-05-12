.PHONY: build run dev-frontend clean

build: build-backend build-frontend

build-backend:
	cd backend && go build -o ../bin/spotman ./cmd/spotman

build-frontend:
	cd frontend && npm run build

run: build-backend
	sudo ./bin/spotman

dev-frontend:
	cd frontend && npm run dev

clean:
	rm -rf bin/
	rm -rf frontend/dist/
