#!/usr/bin/env bash






set -e
declare -a curl_opts=()
curl_opts+=(-silent)
curl_opts+=(--show-error)
curl_opts+=(-I)


 
until curl "${curl_opts[@]}" http://web:8586 > /dev/null ; do
  echo "🔴can't register new web admin user, inobi server is starting, please wait..."
  sleep 10
done
echo "✅inobi server has started"



CODE=$(curl http://web:8586/app/v2/register -H 'Content-Type: application/json' -d '{"name": "Admin", "email": "admin@gmail.com", "username": "admin", "pwd": "aranobi@4456%"}')
if [[ "$CODE" =~ .*200.* ]]; then
    echo '✅registered successfully'
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST --username $POSTGRES_USER --dbname $POSTGRES_DB -f $INSERTION_SQL
elif [[ "$CODE" = 404 ]]; then
    echo '🔴ERROR: server returned HTTP code 404'
else
    echo "🔴ERROR: server returned HTTP code $CODE"
    exit 1
fi