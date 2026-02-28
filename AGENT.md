# AGENT.md — 浙江三位一体快速筛查工具

> 本文件供 AI Coding Agent 阅读，描述项目背景、架构约定和开发规则。
> 每次生成代码前必须完整阅读本文件。

---

## 一、项目背景

面向企业内部升学规划师的 Web 工具，核心功能是：
1. 规划师输入学生的高考成绩 + 学考等级 + 选考科目
2. 系统匹配浙江三位一体招生院校，按「达线 / 接近 / 不达标」分级展示
3. 结果可下载为 Excel 或 PDF

用户规模 < 1000，内部工具，无需高并发设计。

---

## 二、角色体系

```
super_admin  完整权限，含高校数据管理
admin        账号管理，不能操作高校数据
planner      只能使用筛查功能
```

**关键规则**：
- 任何角色都不能修改 / 禁用 / 降级自己
- admin 不能查看或操作 super_admin 账号
- 只有 super_admin 可以访问 `/api/super/*` 路由

---

## 三、项目目录结构

```
project/
├── backend/
│   ├── main.py                  # FastAPI 入口，注册路由
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models.py                # ORM 模型（User, SchoolDataVersion）
│   ├── schemas.py               # Pydantic 请求/响应模型
│   ├── auth.py                  # JWT 生成、校验、依赖注入
│   ├── deps.py                  # 角色权限依赖（require_admin, require_super）
│   ├── matcher.py               # 核心匹配逻辑（已完成，不要修改）
│   ├── school_loader.py         # JSON 加载 + 内存缓存 + 热重载
│   ├── config.py                # 配置项（容差、JWT secret 等）
│   ├── routers/
│   │   ├── auth.py              # /api/auth/*
│   │   ├── match.py             # /api/match
│   │   ├── admin.py             # /api/admin/*（账号管理）
│   │   └── super.py             # /api/super/*（数据管理）
│   ├── scripts/
│   │   └── init_admin.py        # 初始化第一个 super_admin
│   ├── data/
│   │   └── schools/             # JSON 文件存储目录
│   │       ├── v1_schools.json
│   │       └── v2_schools.json
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js         # 路由配置 + 角色守卫
│   │   ├── stores/
│   │   │   ├── auth.js          # 登录态、用户信息、角色
│   │   │   └── schools.js       # 当前数据版本信息
│   │   ├── api/
│   │   │   └── index.js         # Axios 实例 + 拦截器
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── MatchView.vue    # 成绩录入 + 结果展示
│   │   │   ├── AdminView.vue    # 账号管理
│   │   │   └── SuperView.vue    # 数据管理（版本列表、上传、编辑）
│   │   └── components/
│   │       ├── ResultCard.vue   # 单条匹配结果卡片
│   │       ├── MatchForm.vue    # 成绩录入表单
│   │       ├── UserTable.vue    # 账号列表表格
│   │       ├── VersionTable.vue # 版本历史表格
│   │       └── EditGroupModal.vue # 逐条编辑弹窗
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── AGENT.md                     # 本文件
└── RULES.md                     # 编码规范
```

---

## 四、技术栈

### 后端
- Python 3.11+
- FastAPI（路由、依赖注入）
- SQLAlchemy 2.x + SQLite（同步模式，内部工具无需异步 ORM）
- python-jose（JWT，算法 HS256）
- passlib + bcrypt（密码哈希）
- uvicorn（ASGI 服务器）
- pydantic v2（数据校验）

### 前端
- Vue 3（Composition API，`<script setup>` 语法）
- Vite
- Element Plus（UI 组件库）
- Pinia（状态管理）
- Vue Router 4
- Axios
- xlsx（生成 Excel）
- html2canvas + jsPDF（生成 PDF）

---

## 五、数据库模型

### User 表
```python
class User(Base):
    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)   # bcrypt hash
    name       = Column(String, nullable=False)
    role       = Column(String, nullable=False, default="planner")
                 # "super_admin" | "admin" | "planner"
    is_active  = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### SchoolDataVersion 表
```python
class SchoolDataVersion(Base):
    id           = Column(Integer, primary_key=True, autoincrement=True)
    version_no   = Column(Integer, nullable=False)   # 自增版本号
    file_path    = Column(String, nullable=False)     # data/schools/vN_schools.json
    school_count = Column(Integer, nullable=False)
    group_count  = Column(Integer, nullable=False)
    note         = Column(String)
    uploaded_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at  = Column(DateTime, default=datetime.utcnow)
    is_active    = Column(Integer, nullable=False, default=0)
```

---

## 六、核心业务规则

### 匹配逻辑（matcher.py 已实现，不要重写）

`matcher.py` 已完成并测试通过，包含：
- `StudentInput` dataclass
- `MatchResult` dataclass
- `Matcher` 类（`match()` 方法返回 `{"达线": [], "接近": [], "不达标": []}`)
- `result_to_dict()` 序列化函数

调用方式：
```python
from matcher import Matcher, StudentInput, result_to_dict

matcher = Matcher(schools_data)  # schools_data 从 school_loader 获取
results = matcher.match(student_input)
```

### 学考等级
浙江学考等级为 **A / B / C / D / E 五级**，不是 A+/A/B+/B/C，前端下拉选项必须与此一致。

### 高考预审线（preliminary_line）
仅作辅助展示，**不参与达线判断逻辑**。不因预审线不足而降低匹配状态。

### 满分基准
`calcConfig.total_score` 可能是 100 或 750，前端展示学考赋值分时必须同时展示满分基准，避免误解。

### 文字型准入规则（rule_type: "text"）
约 1/3 专业组的准入规则是描述性文字（如「A+B大于等于5」），系统无法自动计算，这类结果统一归入「接近」并标注「需人工核查」，展示 `entry_rule_text` 原文。

### 数据版本热重载
回滚或上传新版本后，`school_loader.py` 必须将新 JSON 加载进内存，**不需要重启进程**。使用全局变量 + reload 函数实现。

---

## 七、API 约定

### 认证
所有需要登录的接口在 Header 中携带：
```
Authorization: Bearer <jwt_token>
```

### 响应格式统一
```json
{
  "code": 0,        // 0=成功，非0=错误
  "msg": "ok",
  "data": {}        // 具体数据
}
```

错误响应：
```json
{
  "code": 4001,
  "msg": "用户名或密码错误",
  "data": null
}
```

### 错误码约定
| 错误码 | 含义 |
|--------|------|
| 4001 | 用户名或密码错误 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 4010 | Token 过期或无效 |
| 4020 | JSON 格式校验失败 |
| 5000 | 服务器内部错误 |

### 角色守卫（后端依赖）
```python
# deps.py
def require_login(token) -> User: ...      # 任意登录用户
def require_admin(user) -> User: ...       # admin 或 super_admin
def require_super(user) -> User: ...       # 仅 super_admin
```

---

## 八、前端路由规划

```
/login                     公开
/match                     需要登录（所有角色）
/admin/users               需要 admin+
/super/data                需要 super_admin
/super/data/:versionId     需要 super_admin（编辑页）
```

路由守卫逻辑（`router/index.js`）：
1. 未登录 → 跳转 `/login`
2. 角色不足 → 跳转 `/match`（不报错，静默降级）

---

## 九、高校 JSON 上传校验规则（后端实现）

上传时必须按顺序执行以下校验，任何一步失败立即返回具体错误信息：

```
1. 文件必须是合法 JSON（能被 json.loads 解析）
2. 顶层必须是 list
3. 每个 school 必须有 id、name、groups 字段
4. 每个 group 必须有 id、name、rules、entry_rule、required_subjects 字段
5. rules 必须包含 A/B/C/D/E 五个键，值为数字
6. entry_rule 必须有 kind 和 score 字段
7. required_subjects_mode 必须是 "and" 或 "or"
```

校验通过后才写入文件系统并入库，旧版本 `is_active` 置 0，新版本 `is_active` 置 1。

---

## 十、开发顺序建议

```
Phase 1（后端基础）
  → database.py + models.py
  → auth.py + deps.py
  → routers/auth.py
  → routers/admin.py
  → school_loader.py
  → routers/match.py（接入 matcher.py）

Phase 2（数据管理后端）
  → routers/super.py（上传、版本列表、回滚、逐条编辑）

Phase 3（前端）
  → 路由 + Pinia store + Axios 实例
  → LoginView
  → MatchView（表单 + 结果卡片）
  → AdminView
  → SuperView

Phase 4（联调 + 部署）
  → Nginx 配置
  → systemd 服务文件
  → HTTPS
```

---

## 十一、不要做的事

- ❌ 不要修改 `matcher.py`（已测试通过）
- ❌ 不要在前端存储或打印 JWT 以外的敏感信息
- ❌ 不要在接口中返回 password 字段，任何情况都不行
- ❌ 不要用 `SELECT *`，始终明确列出需要的字段
- ❌ 不要用同步阻塞方式读写文件（使用 `aiofiles` 或在线程池中执行）
- ❌ 不要在没有校验的情况下直接写入上传的文件
- ❌ 不要跳过 Phase 顺序，后端接口未完成前不要写前端页面
