#!/usr/bin/env bash
# Assemble TaxSabi offline app bundles for Windows, Linux, and macOS.
# Downloads official prebuilt llama.cpp binaries, packs them with the model,
# the app page, and the launchers into distributable archives under dist/.
set -euo pipefail

cd "$(dirname "$0")"

TAG="b10587"
BASE="https://github.com/ggml-org/llama.cpp/releases/download/${TAG}"
GGUF="../model/TaxSabi-1.5B-Q4_K_M.gguf"
DIST="dist"
WORK="$DIST/work"

[[ -f "$GGUF" ]] || { echo "missing $GGUF"; exit 1; }

mkdir -p "$WORK"

fetch() { # url -> file
  local url="$1" out="$2"
  if [[ -f "$out" ]]; then echo "cached: $out"; return 0; fi
  echo "downloading $(basename "$url")..."
  curl -sL --fail -o "$out" "$url"
}

# ---- Windows ---------------------------------------------------------------
if [[ ! -f "$WORK/win/.done" ]]; then
  fetch "$BASE/llama-${TAG}-bin-win-cpu-x64.zip" "$WORK/win-cpu-x64.zip"
  rm -rf "$WORK/win"; mkdir -p "$WORK/win/bins"
  cd "$WORK/win"
  python3 -c "import zipfile; zipfile.ZipFile('../win-cpu-x64.zip').extractall('extract')"
  find extract -type f \( -name "*.exe" -o -name "*.dll" \) -exec cp {} bins/ \;
  touch .done
  cd - >/dev/null
fi

# ---- Linux -----------------------------------------------------------------
# Uses OUR source-built llama-server (glibc 2.31 baseline) so the bundle runs
# on Ubuntu 20.04 as well as the 22.04 audit machine. Verified working build.
if [[ ! -f "$WORK/linux/.done" ]]; then
  rm -rf "$WORK/linux"; mkdir -p "$WORK/linux/bins"
  cp ../tools/llama.cpp-src/build/bin/llama-server "$WORK/linux/bins/"
  # bundle runtime libs so the app is self-contained (works offline of system paths)
  for lib in libstdc++.so.6 libgcc_s.so.1 libgomp.so.1; do
    cp "/usr/lib/x86_64-linux-gnu/$lib" "$WORK/linux/bins/"
  done
  touch "$WORK/linux/.done"
  cd - >/dev/null
fi

# ---- macOS arm64 (Apple Silicon) --------------------------------------------
if [[ ! -f "$WORK/macos/.done" ]]; then
  fetch "$BASE/llama-${TAG}-bin-macos-arm64.tar.gz" "$WORK/macos-arm64.tar.gz"
  rm -rf "$WORK/macos"; mkdir -p "$WORK/macos/bins"
  cd "$WORK/macos"
  mkdir -p extract; tar xzf ../macos-arm64.tar.gz -C extract
  rm -rf bins; mkdir -p bins; cp -a extract/. bins/
  # flatten a nested version folder (e.g. llama-b10587/) so binaries sit directly in bins/
  if [[ ! -f bins/llama-server ]]; then
    for d in bins/llama-*/; do
      [[ -d "$d" ]] && cp -a "$d"/. bins/ && rm -rf "$d"
    done
  fi
  touch .done
  cd - >/dev/null
fi

# ---- Assemble bundles --------------------------------------------------------
assemble() { # name archive bins_dir
  local name="$1" archive="$2" bins="$3"
  local out="$DIST/$name/TaxSabi"
  rm -rf "$DIST/$name"; mkdir -p "$out/bin" "$out/model"
  cp -r "$bins"/. "$out/bin/"
  cp "$GGUF" "$out/model/"
  cp TaxSabi.html "$out/"
  cp Start-TaxSabi.bat Stop-TaxSabi.bat start-taxsabi.sh stop-taxsabi.sh README.md "$out/" 2>/dev/null || true
  chmod +x "$out/start-taxsabi.sh" "$out/stop-taxsabi.sh" 2>/dev/null || true
  cd "$DIST/$name"
  python3 - "$archive" <<'PY'
import sys, tarfile, zipfile, os
archive = sys.argv[1]
if archive.endswith(".zip"):
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk("TaxSabi"):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, p)
else:
    with tarfile.open(archive, "w:gz") as t:
        t.add("TaxSabi")
PY
  cd - >/dev/null
  echo "built $DIST/$archive"
}

rm -rf "$DIST"/TaxSabi-* "$DIST"/*.zip "$DIST"/*.tar.gz 2>/dev/null || true
assemble "windows" "TaxSabi-Setup-Windows.zip"  "$WORK/win/bins"
assemble "linux"   "TaxSabi-Linux.tar.gz"       "$WORK/linux/bins"
assemble "macos"   "TaxSabi-macOS.tar.gz"       "$WORK/macos/bins"

echo
ls -lh "$DIST" | grep -E "zip|tar.gz"
