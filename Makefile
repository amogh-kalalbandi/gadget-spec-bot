build:
	docker-compose up -d --build

shutdown:
	docker-compose down

start_server:
	pip3 install pipenv
	pipenv install --system --deploy && python encode_server/input_encoder.py