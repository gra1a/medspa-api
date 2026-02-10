#!/usr/bin/env bash
# Run tests locally: ensure venv, install deps, start test DB + migrations, run pytest.

set -e
cd "$(dirname "$0")"

COMPOSE="docker compose  -f docker-compose.test.yml"
VENV="${VENV:-.venv}"

# Create venv if missing
if [[ ! -d "$VENV" ]]; then
  echo "Creating venv at $VENV..."
  python3 -m venv "$VENV"
fi

# Install requirements
echo "Installing requirements..."
"$VENV/bin/pip" install -q -r requirements.txt -r requirements-dev.txt

# Start test DB and run migrations
echo "Starting test database..."
$COMPOSE up -d postgres_test
echo "Waiting for postgres_test to be healthy..."
for i in {1..30}; do
  if $COMPOSE exec -T postgres_test pg_isready -U postgres -d medspa_test &>/dev/null; then
    break
  fi
  [[ $i -eq 30 ]] && { echo "postgres_test did not become ready"; exit 1; }
  sleep 1
done
echo "Running schema on test DB..."
$COMPOSE run --rm migrations_test

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5433/medspa_test}"
"$VENV/bin/pytest" tests/ "$@"
exit_code=$?
echo "Stopping test database..."
$COMPOSE down
exit $exit_code
