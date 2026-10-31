#!/bin/sh
# Wrapper around upstream download-libriag.sh (same pattern as go-riagraph).
# Downloads prebuilt libriag into a local cache and writes CMake env flags.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV_FILE="${1:-$PROJECT_DIR/.cache/riag-prebuilt.env}"
CACHE_LIB_DIR="${RIAG_TARGET_DIR:-$PROJECT_DIR/.cache/riag-prebuilt/lib}"
LIB_KIND="${RIAG_LIB_KIND:-static}"
UPSTREAM_SCRIPT="$SCRIPT_DIR/download-libriag.sh"
UPSTREAM_URL="https://raw.githubusercontent.com/cntSafety/RiaGraph/refs/heads/main/scripts/download-libriag.sh"

# Fetch the upstream helper if needed.
if [ ! -f "$UPSTREAM_SCRIPT" ]; then
  echo "Fetching $UPSTREAM_URL ..."
  curl -fsSL "$UPSTREAM_URL" -o "$UPSTREAM_SCRIPT"
  chmod +x "$UPSTREAM_SCRIPT"
fi

RIAG_TARGET_DIR="$CACHE_LIB_DIR" RIAG_LIB_KIND="$LIB_KIND" RIAG_ARCH="${RIAG_ARCH:-}" bash "$UPSTREAM_SCRIPT"

OS="$(uname -s)"
if [ "$LIB_KIND" = "shared" ]; then
  case "$OS" in
    Darwin)
      LIB_PATH="$CACHE_LIB_DIR/libriag.dylib"
      ;;
    Linux)
      LIB_PATH="$CACHE_LIB_DIR/libriag.so"
      ;;
    MINGW*|MSYS*|CYGWIN*)
      LIB_PATH="$CACHE_LIB_DIR/riag_shared.dll"
      ;;
    *)
      echo "Unsupported OS: $OS" >&2
      exit 1
      ;;
  esac
else
  case "$OS" in
    MINGW*|MSYS*|CYGWIN*)
      LIB_PATH="$CACHE_LIB_DIR/riag.lib"
      ;;
    *)
      LIB_PATH="$CACHE_LIB_DIR/libriag.a"
      ;;
  esac
fi

if [ ! -f "$LIB_PATH" ]; then
  echo "Expected precompiled library not found at $LIB_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$ENV_FILE")"
if [ "$LIB_KIND" = "shared" ]; then
  cat > "$ENV_FILE" <<EOF
RIAG_C_API_LIB_PATH=$LIB_PATH
EOF
else
  cat > "$ENV_FILE" <<EOF
EXTRA_CMAKE_FLAGS=-DBUILD_RIAG=FALSE -DBUILD_SHELL=FALSE -DRIAG_API_USE_PRECOMPILED_LIB=TRUE -DRIAG_API_PRECOMPILED_LIB_PATH=$LIB_PATH
EOF
fi

echo "Wrote $ENV_FILE"
echo "Resolved precompiled library: $LIB_PATH"
