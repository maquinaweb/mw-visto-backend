#!/bin/bash

# --- CONFIGURAÇÕES ---
LAMBDA_NAME="mw-sign-test"  # nome exato da função Lambda
URL="https://qmsx5k1j9d.execute-api.sa-east-1.amazonaws.com/test/api/protocols/"
TOKEN=""
COUNT=5
SLEEP_BETWEEN=2

TOTAL=0

echo "🚀 Testando cold start e benchmark da rota $URL"
echo "Função Lambda: $LAMBDA_NAME"
echo "Requisições: $COUNT"
echo "-----------------------------"

for i in $(seq 1 $COUNT)
do
  echo "Forçando cold start #$i..."

  # Força novo container Lambda
  aws lambda update-function-configuration \
    --function-name "$LAMBDA_NAME" \
    --description "force cold start $i $(date +%s)" \
    --profile mw \
    --region sa-east-1 >/dev/null

  # Aguarda a atualização aplicar
  sleep $SLEEP_BETWEEN

  echo "Chamando endpoint..."
  START=$(date +%s%3N)

  # Faz requisição HTTP e mede tempo
  curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Token $TOKEN" \
    "$URL"

  END=$(date +%s%3N)
  DURATION=$((END - START))
  echo -e "\nTempo: ${DURATION} ms\n------\n"

  TOTAL=$((TOTAL + DURATION))
done

AVG=$((TOTAL / COUNT))
echo "⏱  Tempo médio (com cold start): ${AVG} ms"
