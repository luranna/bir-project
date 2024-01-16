# bir-project

Uruchamianie:
uvicorn main:app --ssl-keyfile key.pem --ssl-certfile cert.pem

Testowy request za pomocą programu curl:
curl -k -X 'POST'   'https://127.0.0.1:8000/temperature/'   -H 'accept: application/json'   -H 'Content-Type: application/json'   -d '{
  "temperature": 10
}'