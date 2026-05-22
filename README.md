# 自定义规则仓库

这是一个面向 Surge 和 Mihomo 的轻量规则生成仓库。

你只需要维护根目录的 `domains.txt`，GitHub Actions 会自动生成 `dist/` 下的规则文件，并把这些产物回写到仓库。生成器按客户端官方格式分别输出 Mihomo `classical` rule-provider、Mihomo `domain` rule-provider、Surge `DOMAIN-SET` 和 Surge `RULE-SET`。

## 规则写法

示例：

```txt
[ai]
openai.com
chatgpt.com
@yaml https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.yaml

[direct]
=example.com
apple.com
@list https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Apple/Apple.list
```

语法说明：

- `example.com`：匹配根域名和所有子域名。
- `*.example.com`：会被规范化成 `example.com`。
- `.example.com`：会被规范化成 `example.com`。
- `=api.example.com`：只匹配精确域名 `api.example.com`。
- 分组名如 `[ai]` 会变成输出文件名。
- `@https://...`：自动导入远程 `list` 或 `yaml`。
- `@list <路径或URL>`：按文本规则列表导入。
- `@yaml <路径或URL>`：按 Mihomo `payload:` YAML 导入。

导入时支持这些常见格式：

- 纯域名：`example.com`
- Mihomo 域名写法：`+.example.com`
- Surge DOMAIN-SET 写法：`.example.com`
- 经典规则：`DOMAIN,api.example.com`、`DOMAIN-SUFFIX,example.com`
- 关键词规则：`DOMAIN-KEYWORD,openai`
- Mihomo provider YAML：`payload:` 下的 `- '+.example.com'`

导入语义说明：

- 根 `domains.txt` 里直接写的 `example.com` 仍然表示“根域名 + 子域名”。
- 外部 `list/yaml` 里如果是裸域名 `example.com`，会按规则提供者常见语义当作精确域名处理。
- 如果你希望导入源明确表示后缀匹配，建议使用 `+.example.com`、`.example.com` 或 `DOMAIN-SUFFIX,example.com`。
- Mihomo 默认输出使用官方 `classical` provider：`DOMAIN-SUFFIX,example.com` / `DOMAIN,example.com`。
- 额外输出的 Mihomo `domain` provider 使用 Clash wildcard：`+.example.com` / `example.com`。
- Surge `DOMAIN-SET` 只输出域名和后缀项；`DOMAIN-KEYWORD` 等非 DOMAIN/DOMAIN-SUFFIX 规则只进入 Surge `RULE-SET` 和 Mihomo `classical` provider。

## 重复检测

构建时会自动检测重复项，不再静默去重。

以下情况会直接报错：

- 同一分组里手写重复。
- 手写项和导入项重复。
- 不同分组里出现同一个规则项。

报错信息会带上分组名和来源位置，方便回头清理。

## 本地构建

```bash
python3 scripts/build.py
```

生成产物：

- `dist/mihomo/<group>.yaml`
- `dist/mihomo/<group>.list`
- `dist/mihomo/domain/<group>.yaml`
- `dist/mihomo/domain/<group>.list`
- `dist/surge/domain-set/<group>.txt`
- `dist/surge/rule-set/<group>.list`
- `dist/snippets/mihomo.yaml`
- `dist/snippets/mihomo-domain.yaml`
- `dist/snippets/surge.conf`
- `dist/snippets/surge-rule-set.conf`

## 仓库直链

当前仓库：

- GitHub 仓库：`imNebula/Rules`
- 默认分支：`main`
- 发布分支（构建产物）：`release`

Raw GitHub：

```txt
https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/ai.yaml
https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/ai.list
https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/ai.txt
https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/rule-set/ai.list
```

jsDelivr：

```txt
https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/mihomo/ai.yaml
https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/mihomo/ai.list
https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/surge/domain-set/ai.txt
https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/surge/rule-set/ai.list
```

## GitHub Pages

默认情况下，workflow 只负责构建并提交 `dist/`，不会强依赖 Pages，这样仓库没开 Pages 时也不会构建失败。

如果你也想启用 GitHub Pages：

1. 在仓库设置里把 Pages Source 设置为 `GitHub Actions`。
2. 添加仓库变量 `ENABLE_PAGES=true`。

启用后可用地址：

```txt
https://imnebula.github.io/Rules/mihomo/ai.yaml
https://imnebula.github.io/Rules/mihomo/ai.list
https://imnebula.github.io/Rules/surge/domain-set/ai.txt
https://imnebula.github.io/Rules/surge/rule-set/ai.list
```

生成的 snippets 默认使用 Raw GitHub 地址。若要让 snippets 使用 Pages 地址，可在构建环境设置 `RULES_BASE_URL=https://imnebula.github.io/Rules`。

## 客户端引用示例

Mihomo：

```yaml
rule-providers:
  ai:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/ai.yaml
    path: ./ruleset/ai.yaml
    interval: 86400

rules:
  - RULE-SET,ai,AI
  - MATCH,PROXY
```

如果你明确要使用 Mihomo `domain` provider，可以引用 `dist/snippets/mihomo-domain.yaml` 或 `dist/mihomo/domain/<group>.yaml`。

Surge：

```ini
[Rule]
DOMAIN-SET,https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/ai.txt,AI,extended-matching
FINAL,PROXY
```

如果规则里包含 `DOMAIN-KEYWORD` 等非纯域名规则，应使用 `dist/snippets/surge-rule-set.conf`。
