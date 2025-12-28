#!/bin/bash

echo "Starting Netease Music Downloader..."

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

# 创建必要的目录
mkdir -p downloads

# 检查配置文件是否存在，如果不存在则使用示例配置
if [ ! -f "config.json" ]; then
    echo "⚠️  config.json not found, using config.json.example"
    cp config.json.example config.json
fi

# 启动服务
echo "Starting services..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Services started successfully!"
    echo ""
    echo "📡 Backend API: http://localhost:5000"
    echo "🌐 Frontend UI: http://localhost:3000"
    echo "📁 Downloads: ./downloads/"
    echo ""
    echo "To stop services:"
    echo "  ./docker-stop.sh"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
else
    echo "❌ Failed to start services!"
    exit 1
fi
