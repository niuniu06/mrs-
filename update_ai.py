import urllib.request

V2FLY_BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
ACL4SSR_URL = "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/AI.list"
VPSDance_URL = "https://raw.githubusercontent.com/VPSDance/ai-proxy-rules/main/rules/clash/global.yaml"

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

def parse_acl4ssr():
    content = fetch(ACL4SSR_URL)
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

print("Fetching v2fly...")
parse_v2fly('category-ai-!cn')
print("Fetching acl4ssr...")
parse_acl4ssr()
print("Fetching vpsdance...")
parse_vpsdance()

# 智能去重
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

print(f"Exported {len(final_rules)} domains to ai.txt")
