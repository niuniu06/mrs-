import urllib.request

# --- 基础源 ---
V2FLY_BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
VPSDance_URL = "https://raw.githubusercontent.com/VPSDance/ai-proxy-rules/main/rules/clash/global.yaml"

# --- Clash List 格式源 (ACL4SSR + Blackmatrix7) ---
# 如果以后有更多类似格式的直链，直接按格式加在这里即可！
CLASH_LIST_URLS = {
    "ACL4SSR_AI": "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/AI.list",
    "BM7_OpenAI": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.list",
    "BM7_Claude": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Claude/Claude.list",
    "BM7_Gemini": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/BardAI/BardAI.list",
    "BM7_Copilot": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Copilot/Copilot.list"
}

domains = set()
exact_domains = set()

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Fetch failed for {url}: {e}")
        return ""

def add_domain(d, exact=False):
    # 清理注释、v2ray属性(@!cn)以及引号
    d = d.split('#')[0].split('@')[0].strip().lower()
    d = d.replace("'", "").replace('"', "")
    if not d: return
    # 过滤掉 IP、PROCESS-NAME 或包含空格/斜杠的无效规则 (mrs 仅支持纯域名)
    if ' ' in d or ':' in d or '/' in d: return
        
    if exact:
        exact_domains.add(d)
    else:
        domains.add(d)

def parse_v2fly(name, visited=None):
    if visited is None: visited = set()
    if name in visited: return
    visited.add(name)
    
    content = fetch(V2FLY_BASE_URL + name)
    for line in content.splitlines():
        line = line.split('#')[0].strip()
        if not line: continue
        if line.startswith('include:'):
            include_name = line.split(':')[1].split('@')[0].strip()
            parse_v2fly(include_name, visited)
        elif line.startswith('full:'):
            add_domain(line.split(':')[1], exact=True)
        elif ':' not in line:
            add_domain(line)

# 解析传统的 Clash List (支持 ACL4SSR 和 Blackmatrix7)
def parse_clash_list(url):
    content = fetch(url)
    for line in content.splitlines():
        line = line.split('#')[0].strip()
        if not line: continue
        parts = line.split(',')
        if len(parts) >= 2:
            rule_type = parts[0].strip().upper()
            val = parts[1].strip()
            if rule_type == 'DOMAIN-SUFFIX':
                add_domain(val)
            elif rule_type == 'DOMAIN':
                add_domain(val, exact=True)

def parse_vpsdance():
    content = fetch(VPSDance_URL)
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('- '):
            rule_str = line[2:].strip()
            parts = rule_str.split(',')
            if len(parts) >= 2:
                rule_type = parts[0].strip().upper()
                val = parts[1].strip()
                if rule_type == 'DOMAIN-SUFFIX':
                    add_domain(val)
                elif rule_type == 'DOMAIN':
                    add_domain(val, exact=True)

# ----- 执行抓取流程 -----
print("1. Fetching v2fly category-ai-!cn (包含嵌套include)...")
parse_v2fly('category-ai-!cn')

print("\n2. Fetching Clash List 源 (ACL4SSR & Blackmatrix7)...")
for name, url in CLASH_LIST_URLS.items():
    print(f" -> Fetching {name}...")
    parse_clash_list(url)

print("\n3. Fetching VPSDance...")
parse_vpsdance()

# ----- 智能合并与去重 -----
sorted_domains = sorted(list(domains), key=lambda x: len(x.split('.')))
optimized_domains = set()
for d in sorted_domains:
    parts = d.split('.')
    covered = False
    for i in range(1, len(parts)):
        parent = '.'.join(parts[i:])
        if parent in optimized_domains:
            covered = True
            break
    if not covered:
        optimized_domains.add(d)

final_rules = set()
for d in optimized_domains:
    final_rules.add(f"+.{d}")
for d in exact_domains:
    parts = d.split('.')
    covered = False
    for i in range(len(parts)):
        parent = '.'.join(parts[i:])
        if parent in optimized_domains:
            covered = True
            break
    if not covered:
        final_rules.add(d)

with open('ai.txt', 'w') as f:
    for rule in sorted(list(final_rules)):
        f.write(f"{rule}\n")

print(f"\n✅ All done! Exported {len(final_rules)} domains to ai.txt")
