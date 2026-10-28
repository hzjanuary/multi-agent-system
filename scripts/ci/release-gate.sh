#!/usr/bin/env bash
# Build only from a committed source candidate; evidence stays in ignored private storage.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$REPO_ROOT"
REVISION="$(git rev-parse HEAD)"
IMAGE="${MAOS_RELEASE_IMAGE:-multi-agent-os:spec030-${REVISION:0:12}}"
EVIDENCE="${MAOS_RELEASE_EVIDENCE:-.maos/spec-030/evidence/${REVISION}}"
umask 077
mkdir -p "$EVIDENCE"
python3 scripts/ops/scan_secrets.py --strict --allow-approved-fixtures
python3 scripts/ops/release_artifacts.py index
python3 scripts/ops/release_artifacts.py context --revision "$REVISION"
git archive --format=tar "$REVISION" > "$EVIDENCE/source.tar"
python3 scripts/ops/release_artifacts.py source --revision "$REVISION" --archive "$EVIDENCE/source.tar"
docker build --network="${MAOS_BUILD_NETWORK:-default}" --file backend/Dockerfile --target runtime --build-arg "VCS_REF=$REVISION" --tag "$IMAGE" . > "$EVIDENCE/build.log" 2>&1
python3 scripts/ops/release_artifacts.py image --revision "$REVISION" --image "$IMAGE" | tee "$EVIDENCE/image-verification.json"
docker run --rm --network none --mount "type=bind,source=$REPO_ROOT/scripts/ci/check-release-image.py,target=/verify.py,readonly" "$IMAGE" python /verify.py
printf 'release-image: %s\nsource: %s\n' "$IMAGE" "$REVISION"
