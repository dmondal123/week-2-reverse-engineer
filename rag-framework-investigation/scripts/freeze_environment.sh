#!/usr/bin/env bash

set -euo pipefail

investigation_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repository_root="$(cd "$investigation_root/../.." && pwd)"

python_bin="$investigation_root/.venv/bin/python"

echo "environment_freeze_version=1"
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "investigation_root=$investigation_root"
echo "repository_root=$repository_root"

echo "[python]"
if [ -x "$python_bin" ]; then
    "$python_bin" --version
    "$python_bin" -c 'import platform, sys; print(sys.executable); print(platform.platform())'
    echo "[pip_freeze]"
    "$python_bin" -m pip freeze --all
else
    echo "status=unavailable"
    echo "reason=isolated interpreter not created"
fi

echo "[ollama]"
ollama --version 2>&1 || true
ollama list 2>&1 || true

for model in nomic-embed-text:latest qwen3:4b-instruct-2507-q4_K_M; do
    echo "[ollama_show:$model]"
    ollama show "$model" 2>&1 || true
done

echo "[repositories]"
for spec in \
    "haystack|$investigation_root/vendor/haystack|$repository_root/haystack" \
    "llama_index|$investigation_root/vendor/llama_index|$repository_root/llama_index"; do
    IFS='|' read -r name portable current <<<"$spec"
    path=
    for candidate in "$portable" "$current"; do
        if [ -d "$candidate" ]; then
            candidate_root="$(git -C "$candidate" rev-parse --show-toplevel 2>/dev/null || true)"
            candidate_absolute="$(cd "$candidate" && pwd)"
            if [ -n "$candidate_root" ] && [ "$candidate_root" = "$candidate_absolute" ]; then
                path="$candidate"
                break
            fi
        fi
    done
    echo "[$name]"
    if [ -n "$path" ]; then
        echo "path=$path"
        echo "remote=$(git -C "$path" remote get-url origin 2>/dev/null || echo unavailable)"
        echo "sha=$(git -C "$path" rev-parse HEAD 2>/dev/null || echo unavailable)"
        echo "branch=$(git -C "$path" symbolic-ref --short HEAD 2>/dev/null || echo detached-or-unavailable)"
    else
        echo "status=unavailable"
    fi
done

echo "[configuration_hashes]"
experiment_config="$investigation_root/config/experiment.json"
if [ -f "$experiment_config" ]; then
    shasum -a 256 "$experiment_config"
else
    echo "config/experiment.json: unavailable (Task 2 creates this file)"
fi

find "$investigation_root/config" -maxdepth 1 -type f \
    \( -name 'environment-manifest.json' -o -name 'repository-manifest.json' \) \
    -print0 | sort -z | xargs -0 -r shasum -a 256
