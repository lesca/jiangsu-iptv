import os
import json
import glob
import sys
import requests
from datetime import datetime

def open_latest_tag_file():
    # 获取当前目录中所有json文件
    tag_files = glob.glob(os.path.join('.','*.json'))

    if not tag_files:
        print("当前目录中没有JSON文件。")
        return ""

    # 找出最新的文件
    latest_file = max(tag_files, key=lambda x: os.path.getmtime(x))

    print (f"当前目录中已存在数据文件 {latest_file} ...")
    return latest_file

def read_json_data():
    # 检查命令行参数
    if len(sys.argv) == 2:
        filename = sys.argv[1]  # 获取命令行提供的文件名
    elif len(sys.argv) == 1:
        filename = open_latest_tag_file()   # 读取已经存在的数据文件

    if (filename == ""):
        print ("尝试从URL获取最新数据...")
        # url = 'http://122.96.52.19:29010/tagNewestEpgList/JS_CUCC/1/100/0.json'
        url = 'http://live.epg.gitv.tv/tagNewestEpgList/JS_CUCC/1/100/0.json'
        try:
            # 发送GET请求
            response = requests.get(url)

            # 检查响应状态码
            if response.status_code == 200:
                # 解析JSON数据
                data = response.json()
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.RequestException as e:
            print(f"请求异常：{e}")
    else:
        print (f"读取文件 {filename} ...")
        try:
            # 尝试打开并读取JSON文件
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"文件 {filename} 未找到。")
            sys.exit(1)  # 如果文件不存在，程序退出
        except json.JSONDecodeError:
            print(f"文件 {filename} 不是有效的JSON格式。")
            sys.exit(1)  # 如果文件不是有效的JSON格式，程序退出

    return data

def save_m3u(data, name = "iptv_js"):
    # 获取当前日期和时间
    now = datetime.now()

    # 将日期格式化为 "yyyy-mm-dd"
    date_string = now.strftime('%Y-%m-%d')

    output_latest = f"{name}-latest.m3u"
    output_filename = f"history/{name}-{date_string}.m3u"
    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(data)
    with open(output_latest, 'w', encoding='utf-8') as file:
        file.write(data)

def get_group_info(chnName):
    groups = {
        "少儿": ["少儿","卡通","CCTV-14"],
        "CCTV": ["CCTV","CGTN"],
        "江苏": ["江苏", "南京"],
        "卫视": ["卫视"],
        "教育": ["CETV","教育"],
    }

    for key in groups:
        if any(k in chnName for k in groups[key]):
            return key
    
    return "其他"

def get_js_unicom_source(data):
    m3u_data_full = "#EXTM3U\n"
    m3u_data_kid = "#EXTM3U\n"

    # 从data中提取所需的信息
    for item in data['data']:
        tag = item['tag']
        chnunCode = item['chnunCode']
        chnName = item['chnName']
        chnCode = item['chnCode']
        playUrl = item['playUrl']
        response = requests.get(playUrl)
        # 检查响应状态码
        if response.status_code == 200:
            # 解析JSON数据
            play_data = response.json()
            playUrl_real = play_data['u']
            pass

        # 获取 group 信息
        groupName = get_group_info(chnName)

        # 打印提取的信息
        print(f"处理: {tag}-{chnName}-{chnCode}")
        m3u_data_full += f'#EXTINF:-1 group-title={groupName},{chnName}\n'
        m3u_data_full += f'{playUrl_real}\n'

        # 青少年保护频道过滤
        if all(k not in groupName for k in ["少儿","其他"]):
            m3u_data_kid += f'#EXTINF:-1 group-title={groupName},{chnName}\n'
            m3u_data_kid += f'{playUrl_real}\n'
        
    # 获取custom目录下所有的文件
    custom_files = glob.glob(os.path.join('custom', '*.m3u'))
    custom_data = ""
    # 遍历所有找到的文件
    for custom_file in custom_files:
        # 读取当前文件的内容
        with open(custom_file, 'r', encoding='utf-8') as file:
            content = file.readlines()
        custom_data += "".join(content)

    m3u_data_full += custom_data
    m3u_data_kid += custom_data

    # 保存
    save_m3u(data = m3u_data_full, name="iptv_js_full")
    save_m3u(data = m3u_data_kid, name = "iptv_js_kid")
    print("Done.")


if __name__ == "__main__":
    data = read_json_data()
    get_js_unicom_source(data)
    
