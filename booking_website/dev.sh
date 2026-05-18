vite &
VITE_PID=$!

json-server -w --port=3333 db.json &
JSON_SERVER_PID=$!

# Define a function to kill both processes
cleanup() {
  echo "Stopping Vite and JSON Server..."
  kill $VITE_PID
  kill $JSON_SERVER_PID
  exit
}

trap cleanup INT

wait $VITE_PID
wait $JSON_SERVER_PID
