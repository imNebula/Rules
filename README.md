# 🛠️ Custom Rules - 轻量化规则订阅生成器

这是一个面向 **Mihomo (Clash)** 和 **Surge** 的轻量化、自动化的规则生成与部署方案。

你只需要在根目录下维护 `domains.txt`，其余工作（规则解析、合并去重、多格式构建、分支发布、Pages 部署）全部由本地脚本和 GitHub Actions 自动化完成。

---

## 🚀 快速上手 (使用流程)

使用本项目非常简单，主要包含以下几个步骤：

### 1. 编辑规则
在根目录下的 [`domains.txt`](file:///Users/noxsk/Git/Rules/domains.txt) 中维护你的规则列表。支持使用分组标记、直接书写域名，或通过 `@list` / `@yaml` 导入外部规则订阅。详情参考 [规则写法](#-规则写法)。

### 2. 本地构建与测试（可选）
本项目构建脚本**无任何第三方依赖**，仅需系统内置的 Python 3 即可运行。在提交代码前，你可以在本地运行以下命令，以验证规则是否正确，或检查是否有冲突和重复项：
```bash
python3 scripts/build.py
```
构建成功后，会在本地生成 `dist/` 目录，你可在此目录中查看生成的各种格式的规则文件（注意：`dist/` 目录已在 `.gitignore` 中忽略，不会被提交到 `main` 分支）。

### 3. 提交并推送
将你的修改（主要是 `domains.txt`）提交并推送到 GitHub 的 `main` 分支：
```bash
git add domains.txt
git commit -m "feat: 更新自定义规则"
git push origin main
```

### 4. 自动部署与发布
推送后，GitHub Actions 工作流会自动运行：
1. **自动构建**：在 GitHub 容器中执行构建脚本，编译生成所有客户端格式的规则文件。
2. **推送至发布分支**：自动将生成的 `dist/` 目录内容强推（Force Push）到仓库的 `release` 分支。
3. **部署 Pages (可选)**：如果启用了 GitHub Pages，会自动将构建产物部署到 Pages 站点。

### 5. 客户端订阅
在你的 Mihomo (Clash) 或 Surge 配置文件中，直接引用 `release` 分支下的直链或 Pages 链接。详情参考 [客户端配置示例](#-客户端配置示例)。

---

## 📋 快速复制直链

以下是当前仓库中已定义分组 (`uzu`, `fast`) 以及全局配置片段的订阅直链。您可直接点击代码块右上角的 **Copy** 按钮进行复制：

<details>
<summary><b>点击展开 / 折叠：<code>uzu</code> 分组规则链接</b></summary>

- **Mihomo (Clash) Classical YAML**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/uzu.yaml
  ```
- **Mihomo (Clash) Domain YAML**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/domain/uzu.yaml
  ```
- **Surge DOMAIN-SET**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/uzu.txt
  ```
- **Surge RULE-SET**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/rule-set/uzu.list
  ```
</details>

<details>
<summary><b>点击展开 / 折叠：<code>fast</code> 分组规则链接</b></summary>

- **Mihomo (Clash) Classical YAML**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/fast.yaml
  ```
- **Mihomo (Clash) Domain YAML**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/domain/fast.yaml
  ```
- **Surge DOMAIN-SET**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/fast.txt
  ```
- **Surge RULE-SET**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/rule-set/fast.list
  ```
</details>

<details>
<summary><b>点击展开 / 折叠：全局配置片段 (Snippets) 链接</b></summary>

- **Mihomo (Clash) Classical Snippet**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/snippets/mihomo.yaml
  ```
- **Mihomo (Clash) Domain Snippet**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/snippets/mihomo-domain.yaml
  ```
- **Surge DOMAIN-SET Snippet**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/snippets/surge.conf
  ```
- **Surge RULE-SET Snippet**:
  ```text
  https://raw.githubusercontent.com/imNebula/Rules/release/dist/snippets/surge-rule-set.conf
  ```
</details>

---

## 📝 规则写法

在 [`domains.txt`](file:///Users/noxsk/Git/Rules/domains.txt) 中编写规则，支持分组、域名规则、精确匹配以及外部规则导入。

### 语法示例
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

### 语法说明
- **分组名称**：例如 `[ai]`，对应的规则会被输出为名为 `ai` 的规则文件。分组名只能包含小写字母、数字、下划线和连字符 `[a-z0-9_-]`。
- **后缀匹配**：直接写 `example.com`、`*.example.com` 或 `.example.com`，均会自动规范化为 `example.com`，匹配该域名及其所有子域名。
- **精确匹配**：以 `=` 开头（如 `=api.example.com`），仅精确匹配该域名本身，不匹配其子域名。
- **远程导入**：
  - `@list <URL或本地路径>`：按普通文本规则列表导入。
  - `@yaml <URL或本地路径>`：按 Mihomo YAML payload 规则列表导入。
  - `@https://...` 或 `@/path/...`：自动根据后缀名（`.yaml` / `.yml` 导入为 yaml，其他导入为 list）判断格式。

### 导入格式兼容性
支持导入以下常见的规则格式，脚本会自动提取并解析为统一的域名项：
- 裸域名：`example.com`
- 带有通配符的域名：`+.example.com` 或 `.example.com`
- 经典规则行：`DOMAIN,api.example.com`、`DOMAIN-SUFFIX,example.com`、`HOST,api.example.com`、`HOST-SUFFIX,example.com`
- 关键词规则行：`DOMAIN-KEYWORD,openai`
- Mihomo YAML payload：如 `- '+.example.com'` 或 `- 'DOMAIN-SUFFIX,example.com'`

> [!NOTE]
> 外部 `list/yaml` 中如果是裸域名 `example.com`，为符合常见规则源的习惯，会被当作**精确域名**匹配（即 `=example.com`）处理。如果希望表示后缀匹配，请在外部源中使用 `+.example.com`、`.example.com` 或 `DOMAIN-SUFFIX,example.com`。

---

## 🔍 重复规则检测

为了保证规则性能及配置文件的整洁，构建脚本会在编译时进行严格的去重和冲突检测。以下情况会导致**构建报错并中断**：
- 同一分组内手动书写了重复的规则。
- 手动编写的规则项与通过 `@list`/`@yaml` 导入的外部规则重复。
- 不同的分组中出现了同一条规则（避免分流歧义）。

报错时会输出详细的冲突域名、所在分组及来源位置（如行号或 URL），方便快速定位并清理。

---

## 📦 生成产物目录

运行构建后，`dist/` 目录下将生成以下结构的文件：

```text
dist/
├── mihomo/
│   ├── <group>.yaml              # Mihomo classical 格式 YAML Payload
│   ├── <group>.list              # Mihomo classical 格式纯文本规则
│   └── domain/
│       ├── <group>.yaml          # Mihomo domain 格式 YAML Payload (仅限域名项)
│       └── <group>.list          # Mihomo domain 格式纯文本规则 (仅限域名项)
├── surge/
│   ├── domain-set/
│   │   └── <group>.txt           # Surge DOMAIN-SET 格式 (最适合大容量域名匹配)
│   └── rule-set/
│       └── <group>.list          # Surge RULE-SET 格式 (包含 DOMAIN-KEYWORD 等)
└── snippets/
    ├── mihomo.yaml               # 预生成的 Mihomo classical 策略组与配置片段
    ├── mihomo-domain.yaml        # 预生成的 Mihomo domain 策略组与配置片段
    ├── surge.conf                # 预生成的 Surge DOMAIN-SET 规则片段
    └── surge-rule-set.conf       # 预生成的 Surge RULE-SET 规则片段
```

---

## 🔗 订阅链接直链

### 1. 默认 GitHub Raw 链接
默认使用 `release` 分支进行直链订阅。链接格式如下：
- **Mihomo (Classical)**: `https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/<group>.yaml`
- **Mihomo (Domain)**: `https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/domain/<group>.yaml`
- **Surge (Domain-Set)**: `https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/<group>.txt`
- **Surge (Rule-Set)**: `https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/rule-set/<group>.list`

### 2. CDN 加速链接 (jsDelivr)
- **Mihomo**: `https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/mihomo/<group>.yaml`
- **Surge**: `https://cdn.jsdelivr.net/gh/imNebula/Rules@release/dist/surge/domain-set/<group>.txt`

### 3. GitHub Pages 部署 (可选)
如果不想依赖 GitHub Raw 链接，可以启用 GitHub Pages 服务：
1. 前往仓库的 **Settings** -> **Pages**。
2. 将 **Build and deployment** 的 Source 设置为 **GitHub Actions**。
3. 前往 **Settings** -> **Secrets and variables** -> **Variables**，添加一个仓库变量：
   - 名称：`ENABLE_PAGES`
   - 值：`true`
4. （可选）如果你绑定了自定义域名或需要指定基础 URL，可在 Variables 中添加 `RULES_BASE_URL` 变量，值为你的 Pages 访问地址（例如 `https://rules.example.com`），这样生成的 snippets 中的订阅链接就会自动使用该地址。

启用后，订阅地址为：
`https://imnebula.github.io/Rules/mihomo/<group>.yaml`

---

## ⚙️ 客户端配置示例

### Mihomo (Clash)
```yaml
rule-providers:
  ai:
    type: http
    behavior: classical
    format: yaml
    url: "https://raw.githubusercontent.com/imNebula/Rules/release/dist/mihomo/ai.yaml"
    path: ./ruleset/ai.yaml
    interval: 86400

rules:
  - RULE-SET,ai,AI
  - MATCH,PROXY
```
> 若使用 `domain` 类型的 provider，可将 behavior 设为 `domain`，并将 URL 指向 `dist/mihomo/domain/ai.yaml`。

### Surge
```ini
[Rule]
# 针对纯域名推荐使用 DOMAIN-SET (更高效，支持子域名匹配)
DOMAIN-SET,https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/domain-set/ai.txt,AI,extended-matching

# 包含 DOMAIN-KEYWORD 等复杂规则时，使用 RULE-SET
RULE-SET,https://raw.githubusercontent.com/imNebula/Rules/release/dist/surge/rule-set/ai.list,AI

FINAL,PROXY
```
