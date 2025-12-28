#!/bin/bash

# 设置字符编码
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo
echo "========================================"
echo "   网易云音乐下载器 - Linux停止服务脚本"
echo "========================================"
echo

echo "⏳ 正在停止服务..."

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🔴 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        
        # 检查是否成功停止
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "⚠️  后端服务未正常停止，强制终止..."
            kill -9 $BACKEND_PID
        fi
        echo "✅ 后端服务已停止"
        rm -f backend.pid
    else
        echo "ℹ️  后端服务未运行"
        rm -f backend.pid
    fi
else
    echo "ℹ️  后端服务未运行（未找到PID文件）"
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🔴 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        
        # 检查是否成功停止
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "⚠️  前端服务未正常停止，强制终止..."
            kill -9 $FRONTEND_PID
        fi
        echo "✅ 前端服务已停止"
        rm -f frontend.pid
    else
        echo "ℹ️  前端服务未运行"
        rm -f frontend.pid
    fi
else
    echo "ℹ️  前端服务未运行（未找到PID文件）"
fi

# 清理可能残留的进程
if pgrep -f "python.*main.py" > /dev/null; then
    echo "🔴 清理残留的后端进程..."
    pkill -f "python.*main.py"
    sleep 1
fi

if pgrep -f "npm.*run.*dev" > /dev/null; then
    echo "🔴 清理残留的前端进程..."
    pkill -f "npm.*run.*dev"
    sleep 1
fi

echo
echo "========================================"
echo "   ✅ 所有服务已停止"
echo "========================================"
echo
