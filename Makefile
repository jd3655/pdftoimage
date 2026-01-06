.PHONY: dev backend frontend build-web

dev:
	@echo "Run backend and frontend in separate terminals"
	@echo "Terminal 1: pdftoimage"
	@echo "Terminal 2: cd frontend && npm run dev"

backend:
	pdftoimage

frontend:
	cd frontend && npm run dev

build-web:
	cd frontend && npm install && npm run build
	mkdir -p pdftoimage/web
	rm -rf pdftoimage/web/dist
	cp -r frontend/dist pdftoimage/web/
