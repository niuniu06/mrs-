import os
import re
import urllib.request
import subprocess
import ipaddress

SOURCE_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/adblockdns.txt"
CLEAN_TXT = "ads.txt"
OUTPUT_MRS = "ads.mrs"

def is_ip(addr):
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False

def download_and_clean():
    print("1. 正在下载 GOODBYEADS dns.txt...")
    req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8', errors='ignore')

    print("2. 正在提取并清洗规则...")
    domains = set()
    pattern = re.compile(r"^\|\|([a-zA-Z0-9_\-\.\*]+)\^")

    for line in content.splitlines():
        line = line.strip()
        # 跳过注释、段落标头和白名单
        if not line or line.startswith(('!', '[', '#', '@@')):
            continue
        
        match = pattern.match(line)
        if match:
            domain = match.group(1).lower()
            # 移除开头的通配符 *. 或 .
            if domain.startswith('*.'):
                domain = domain[2:]
            elif domain.startswith('.'):
                domain = domain[1:]
            
            # 简单验证合法域名格式，且排除纯 IP
            if '.' in domain and not is_ip(domain) and not domain.startswith('*'):
                domains.add(domain)

    # 排序保存为纯文本列表
    sorted_domains = sorted(list(domains))
    with open(CLEAN_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_domains) + "\n")
    print(f"清洗完成，共提取 {len(sorted_domains)} 条有效域名规则 -> {CLEAN_TXT}")

def build_mrs():
    print("3. 正在调用 Mihomo 编译为 .mrs...")
    # 请确保系统环境变量中有 mihomo，或者指定为绝对路径（如 ./mihomo.exe）
    cmd = ["mihomo", "convert-ruleset", "domain", "text", CLEAN_TXT, OUTPUT_MRS]
    try:
        subprocess.run(cmd, check=True)
        print(f"转换成功！生成文件：{OUTPUT_MRS} (大小: {os.path.getsize(OUTPUT_MRS) / 1024:.2f} KB)")
    except FileNotFoundError:
        print("错误：未找到 mihomo 可执行文件，请先下载 mihomo 并放入 PATH。")

if __name__ == "__main__":
    download_and_clean()
    build_mrs()
