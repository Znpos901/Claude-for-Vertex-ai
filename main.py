#!/usr/bin/env python3

import os
import sys
# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
import json
import time
import subprocess
import colorama
import pkg_resources
import importlib.util
import globalVar


def check_requirements():
    if getattr(sys, 'frozen', False):
        print("从可执行文件启动，跳过依赖项检查。")
        return True
    print("检查依赖项...")
    requirements_file = "requirements.txt"
    
    # 读取 requirements.txt 文件
    with open(requirements_file, 'r') as f:
        requirements = f.read().splitlines()
    
    # 检查每个依赖项
    missing = []
    for requirement in requirements:
        try:
            pkg_resources.require(requirement)
        except pkg_resources.DistributionNotFound:
            missing.append(requirement)
    
    if missing:
        print("错误: 以下依赖项缺失:")
        for req in missing:
            print(f" - {req}")
        user_input = input("是否运行 'pip install -r requirements.txt' 来安装所需依赖？(y/n): ").strip().lower()
        if user_input == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
                print("依赖项已安装。请重新运行脚本。")
            except subprocess.CalledProcessError:
                print("安装依赖项时出错。请手动检查并安装所需依赖。")
            sys.exit(1)
        else:
            print("取消安装依赖项。")
            return False
    else:
        print("所有依赖项检查通过。")
        return True

#获取目录位置
def get_base_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是普通Python脚本
        return os.path.dirname(os.path.abspath(__file__))

def check_directory_structure():
    # 检查当前目录
    app_base_dir = get_base_path()

    # 检查json文件是否有效
    print(f"检查 json文件是否有效..")
    start_count = globalVar.accountdata.count("{")
    end_count = globalVar.accountdata.count("}")
    if start_count != end_count:
        print(f"错误: 开始标志数量为 {start_count} ,结束标志数量为 {end_count} , 数量不匹配！")
        return False
    time.sleep(0.1)
    
    # 检查 model_mapping.json 文件
    print(f"检查 model_mapping.json 文件..")
    model_mapping_file = os.path.join(app_base_dir, 'model_mapping.json')
    if not os.path.exists(model_mapping_file):
        print(f"错误: {app_base_dir}下 'model_mapping.json'模型配置文件缺失！")
        return False
    time.sleep(0.1)
    
    # 检查 model_mapping.json 的内容
    print(f"检查 model_mapping.json 的内容..")
    try:
        with open(model_mapping_file, 'r') as f:
            json.load(f)
    except json.JSONDecodeError:
        print(f"Error: 'model_mapping.json' 内容不可用，请检查。")
        return False
    time.sleep(0.2)
    
    return True

def manage_gcp_auth():
    # 检查是否有激活的服务账号
    check_cmd = "gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q '@.*\\.iam\\.gserviceaccount\\.com'"
    if subprocess.run(check_cmd, shell=True).returncode == 0:
        print("GCP 服务账号已激活。")
    else:
        print("激活 GCP 服务账号...")
        key_file = os.path.join('auth', 'service-account-key.json')
        activate_cmd = f"gcloud auth activate-service-account --key-file={key_file}"
        subprocess.run(activate_cmd, shell=True, check=True)

def load_proxy_server():
    if getattr(sys, 'frozen', False):
        module_path = os.path.join(sys._MEIPASS, 'proxy_server.py')
    else:
        module_path = 'proxy_server.py'
    
    spec = importlib.util.spec_from_file_location("proxy_server", module_path)
    proxy_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy_server)
    return proxy_server


def main():
    if not check_requirements():
        input("依赖项未满足。请安装后重启。")
        sys.exit(1)
        
    if not check_directory_structure():
        input("目录必要文件验证失败，取消启动。")
        sys.exit(1)
    
    print("目录文件验证成功。")
#    manage_gcp_auth()
    
    # 启动 proxy_server.py
#    time.sleep(0.5)
    print("启动服务器...")
    colorama.init()
    proxy_server = load_proxy_server()

    import uvicorn
    uvicorn.run(proxy_server.app, host=proxy_server.hostaddr, port=proxy_server.lsnport)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        time.sleep(1)
        sys.exit(0)
