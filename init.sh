#!/bin/bash
set -e

echo "=== Harness Initialization ==="

echo "=== cd apps/web && npm run lint ==="
(cd apps/web && npm run lint)

echo "=== cd apps/web && npm run build ==="
(cd apps/web && npm run build)

echo "=== cd apps/api && python -m compileall app ==="
(cd apps/api && python -m compileall app)

echo "=== cd apps/api && python -m pytest tests/ ==="
(cd apps/api && python -m pytest tests/)

echo "=== cd packages/gpu-worker && python -m compileall worker ==="
(cd packages/gpu-worker && python -m compileall worker)

echo "=== cd packages/gpu-worker && python -m pytest tests/ ==="
(cd packages/gpu-worker && python -m pytest tests/)

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Read feature_list.json to see current feature state"
echo "2. Pick ONE unfinished feature to work on"
echo "3. Implement only that feature"
echo "4. Re-run verification before claiming done"
