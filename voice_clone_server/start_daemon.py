#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以守护进程方式启动语音克隆服务
"""

import subprocess
import sys
import os
import time

def main():
    server_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(server_dir, "server.py")
    log_file = os.path.join(server_dir, "server.log")

    # 检查是否已经在运行
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8003))
    sock.close()

    if result == 0:
        print("服务已经在运行!")
        return

    print("启动语音克隆服务...")
    print(f"日志文件: {log_file}")

    # Windows 使用 CREATE_NEW_PROCESS_GROUP 和 DETACHED_PROCESS
    if sys.platform == 'win32':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000

        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                [sys.executable, server_script],
                cwd=server_dir,
                stdout=log,
                stderr=log,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
            )
        print(f"服务进程已启动，PID: {process.pid}")
    else:
        # Unix 系统
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                [sys.executable, server_script],
                cwd=server_dir,
                stdout=log,
                stderr=log,
                start_new_session=True
            )
        print(f"服务进程已启动，PID: {process.pid}")

    # 等待服务启动
    print("等待服务就绪...")
    for i in range(30):
        time.sleep(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8003))
        sock.close()
        if result == 0:
            print(f"\n服务已启动! 端口: 8003")
            print(f"API 文档: http://localhost:8003/docs")
            print(f"健康检查: http://localhost:8003/health")
            return
        print(".", end="", flush=True)

    print("\n服务启动超时，请检查日志文件")
    with open(log_file, 'r') as f:
        print(f.read())


if __name__ == "__main__":
    main()
