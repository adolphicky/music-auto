#!/bin/bash

echo "Building Netease Music Downloader Docker image..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# 构建镜像
echo "Building Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "To run the application:"
    echo "  ./docker-run.sh"
else
    echo "❌ Docker build failed!"
    exit 1
fi
