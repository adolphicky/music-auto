#!/bin/bash

echo "Stopping Netease Music Downloader..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

# 停止服务
echo "Stopping services..."
docker-compose down

if [ $? -eq 0 ]; then
    echo "✅ Services stopped successfully!"
else
    echo "❌ Failed to stop services!"
    exit 1
fi
