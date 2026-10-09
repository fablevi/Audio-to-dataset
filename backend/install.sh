#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/CrispStrobe/CrispASR.git"
PROJECT_DIR="CrispASR"

echo "=========================================="
echo " CrispASR Automated Installer & Setup"
echo "=========================================="

for cmd in git cmake curl; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required command '$cmd' is not installed or not in PATH."
        exit 1
    fi
done

echo "-> Checking for yt-dlp..."
if ! command -v yt-dlp &> /dev/null; then
    echo "-> yt-dlp not found. Installing latest binary to /usr/local/bin..."
    sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
    sudo chmod a+rx /usr/local/bin/yt-dlp
    echo "-> yt-dlp installed successfully."
else
    echo "-> yt-dlp is already installed."
fi

echo "Select GPU backend for C++ build:"
echo "1) CUDA (NVIDIA)"
echo "2) Vulkan (AMD/Intel/Cross-platform)"
echo "3) SYCL (Intel OneAPI)"
read -p "Enter choice [1-3]: " GPU_CHOICE

EXTRA_CMAKE_FLAGS=""

case $GPU_CHOICE in
    1)
        CUDA_HOST_COMPILER=""
        for gcc_ver in g++-15 g++-14 g++-13; do
            if command -v "$gcc_ver" &> /dev/null; then
                CUDA_HOST_COMPILER=$(command -v "$gcc_ver")
                break
            fi
        done

        HOST_COMPILER_FLAG=""
        if [ -n "$CUDA_HOST_COMPILER" ]; then
            echo "-> Found supported CUDA host compiler: $CUDA_HOST_COMPILER"
            HOST_COMPILER_FLAG="-DCMAKE_CUDA_HOST_COMPILER=$CUDA_HOST_COMPILER"
        else
            echo "-> Warning: No older GCC host compiler found. Defaulting to system g++."
        fi

        EXTRA_CMAKE_FLAGS="-DGGML_CUDA=ON $HOST_COMPILER_FLAG -DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler"
        BACKEND_NAME="CUDA"
        ;;
    2)
        EXTRA_CMAKE_FLAGS="-DGGML_VULKAN=ON"
        BACKEND_NAME="Vulkan"
        ;;
    3)
        EXTRA_CMAKE_FLAGS="-DGGML_SYCL=ON"
        BACKEND_NAME="SYCL"
        ;;
    *)
        echo "Invalid selection. Exiting."
        exit 1
        ;;
esac

echo "-> Selected: $BACKEND_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "-> CrispASR directory not found. Cloning repository..."
    git clone --recursive "$REPO_URL" "$PROJECT_DIR"
else
    echo "-> CrispASR directory already exists. Skipping clone."
fi

cd "$PROJECT_DIR"

if [ -d "build" ]; then
    echo "-> Cleaning existing build directory..."
    rm -rf build
fi

echo "-> Building C++ binary ($BACKEND_NAME backend)..."
cmake -B build $EXTRA_CMAKE_FLAGS -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)

LIB_PATH=$(find "$(pwd)/build" -name "libcrispasr.so" | head -n 1)
cd ..

if [ -z "$LIB_PATH" ] || [ ! -f "$LIB_PATH" ]; then
    echo "Error: libcrispasr.so not found inside build directory. Build failed."
    exit 1
fi

echo "-> Found library at: $LIB_PATH"

EXPORT_LINE="export CRISPASR_LIB_PATH=\"$LIB_PATH\""

if grep -q "CRISPASR_LIB_PATH" ~/.bashrc; then
    echo "-> Updating CRISPASR_LIB_PATH in ~/.bashrc..."
    sed -i "/CRISPASR_LIB_PATH/c\\$EXPORT_LINE" ~/.bashrc
else
    echo "-> Adding CRISPASR_LIB_PATH to ~/.bashrc..."
    echo "" >> ~/.bashrc
    echo "# CrispASR Library Path" >> ~/.bashrc
    echo "$EXPORT_LINE" >> ~/.bashrc
fi

export CRISPASR_LIB_PATH="$LIB_PATH"

echo "=========================================="
echo " INSTALLATION SUCCESSFUL"
echo "=========================================="
echo "Run the following command to apply environment variables:"
echo "  source ~/.bashrc"