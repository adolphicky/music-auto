#!/bin/bash

# 设置字符编码
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo
echo "========================================"
echo "   网易云音乐下载器 - Linux一键启动脚本"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未检测到Python 3，请先安装Python 3.7+"
    echo "   安装命令：sudo apt install python3 python3-pip  # Ubuntu/Debian"
    echo "            sudo yum install python3 python3-pip  # CentOS/RHEL"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误：未检测到Node.js，请先安装Node.js"
    echo "   下载地址：https://nodejs.org/"
    exit 1
fi

echo "✅ 环境检查通过"
echo

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo "🔧 激活Python虚拟环境..."
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
    echo
fi

# 安装Python依赖
if [ -f "requirements.txt" ]; then
    echo "📦 正在安装Python依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "⚠️  Python依赖安装失败，尝试继续启动..."
    else
        echo "✅ Python依赖安装完成"
    fi
    echo
fi

# 安装前端依赖
if [ -f "package.json" ]; then
    echo "📦 正在安装前端依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "⚠️  前端依赖安装失败，尝试继续启动..."
    else
        echo "✅ 前端依赖安装完成"
    fi
    echo
fi

# 创建下载目录
if [ ! -d "downloads" ]; then
    mkdir downloads
    echo "📁 创建下载目录：downloads"
    echo
fi

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "⚠️  未找到config.json配置文件，将使用默认配置"
    echo
fi

# 检查是否已有服务在运行
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  检测到后端服务已在运行，先停止现有服务..."
    pkill -f "python.*main.py"
    sleep 2
fi

if pgrep -f "npm.*run.*dev" > /dev/null; then
    echo "⚠️  检测到前端服务已在运行，先停止现有服务..."
    pkill -f "npm.*run.*dev"
    sleep 2
fi

# 清理旧的PID文件
rm -f backend.pid frontend.pid

# 启动后端服务（后台运行）
echo "🚀 启动后端服务（端口：5000）..."
nohup python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid
echo "✅ 后端服务已启动，PID: $BACKEND_PID"

# 等待后端服务启动
echo "⏳ 等待后端服务启动（5秒）..."
sleep 5

# 检查后端服务是否正常启动
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health | grep -q "200"; then
    echo "✅ 后端服务健康检查通过"
else
    echo "⚠️  后端服务健康检查失败，但继续启动前端..."
    echo "    请检查日志文件：backend.log"
fi
echo

# 启动前端服务（后台运行）
echo "🚀 启动前端服务（端口：3000）..."
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid
echo "✅ 前端服务已启动，PID: $FRONTEND_PID"

# 等待前端服务启动
echo "⏳ 等待前端服务启动（8秒）..."
sleep 8

# 检查前端服务是否正常启动
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo "✅ 前端服务健康检查通过"
else
    echo "⚠️  前端服务健康检查失败，但服务可能仍在启动中..."
    echo "    请检查日志文件：frontend.log"
fi
echo

echo
echo "========================================"
echo "   服务启动信息"
echo "========================================"
echo "📡 后端API服务：http://localhost:5000"
echo "🌐 前端界面：http://localhost:3000"
echo "📁 下载目录：downloads/"
echo "📋 日志文件：backend.log, frontend.log"
echo "🔧 进程PID：后端($BACKEND_PID), 前端($FRONTEND_PID)"
echo
echo "✅ 所有服务已成功启动！"
echo "⚠️  使用 './stop.sh' 停止所有服务"
echo "========================================"
echo
