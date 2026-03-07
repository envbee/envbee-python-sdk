#!/bin/bash
set -euo pipefail

PYTHON_VERSIONS=("3.10" "3.11" "3.12" "3.13" "3.14")

echo "🐍 Starting matrix test with Python versions: ${PYTHON_VERSIONS[*]}"
echo

for version in "${PYTHON_VERSIONS[@]}"; do
  echo "🔹 Testing with Python $version..."

  docker run --rm \
    -v "$PWD/..":/app \
    -w /app \
    python:$version \
    bash -c "
      pip install .
      python -m unittest discover
    " || {
      echo "❌ Tests failed on Python $version"
      exit 1
    }

  echo "✅ Tests passed on Python $version"
  echo
done

echo "🎉 All Python versions passed successfully."
