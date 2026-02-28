# RULES.md — 编码规范

> 本文件定义项目的代码风格、安全规则和质量要求。
> AI Agent 生成的所有代码必须符合以下规范。

---

## 一、通用规则

- 所有代码和注释使用**中文注释**，变量/函数/类名使用**英文**
- 每个文件顶部写明文件用途的单行注释
- 禁止出现魔法数字，常量统一在 `config.py`（后端）或 `constants.js`（前端）中定义
- 不要留下 `TODO` / `FIXME` 注释，要么实现，要么在 AGENT.md 中记录
- 每个函数只做一件事，超过 40 行的函数必须拆分

---

## 二、后端规范（Python / FastAPI）

### 2.1 文件结构

```python
# 文件顶部注释
"""
auth.py — JWT 生成与校验，登录依赖注入
"""

# 标准库
import os
from datetime import datetime

# 第三方库
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

# 本地模块
from database import get_db
from models import User
```

导入顺序：标准库 → 第三方库 → 本地模块，三组之间空一行。

### 2.2 路由规范

```python
# ✅ 正确：路由函数命名清晰，有类型注解，有响应模型
@router.post("/login", response_model=schemas.LoginResponse)
async def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    ...

# ❌ 错误：无类型注解，无响应模型
@router.post("/login")
def login(body, db):
    ...
```

- 所有路由函数必须有 `response_model`
- 所有参数必须有类型注解
- 路由函数命名：`动词_名词`，如 `get_users`、`create_user`、`rollback_version`

### 2.3 Pydantic Schema 规范

```python
# schemas.py

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "planner"

    @field_validator("role")
    def role_must_be_valid(cls, v):
        if v not in ("super_admin", "admin", "planner"):
            raise ValueError("角色值无效")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    # ❌ 绝对不能有 password 字段
    model_config = ConfigDict(from_attributes=True)
```

- Request schema 和 Response schema 分开定义，**Response 中绝对不包含 password**
- 所有 schema 都要写字段校验器（validator）
- 使用 `model_config = ConfigDict(from_attributes=True)` 支持 ORM 对象

### 2.4 错误处理

```python
# ✅ 正确：使用统一错误格式
from fastapi import HTTPException
from fastapi.responses import JSONResponse

def api_error(code: int, msg: str):
    return JSONResponse(
        status_code=200,  # HTTP 状态码统一 200，业务错误码在 body 中
        content={"code": code, "msg": msg, "data": None}
    )

def api_ok(data=None, msg="ok"):
    return {"code": 0, "msg": msg, "data": data}

# 使用示例
if not user:
    return api_error(4001, "用户名或密码错误")
```

- HTTP 状态码统一返回 200，业务错误通过 `code` 字段区分
- 不要暴露系统内部错误信息（如数据库报错）给前端，统一返回 5000

### 2.5 数据库操作

```python
# ✅ 正确：明确列出字段，关闭 session
def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

# ❌ 错误：不要在路由函数里直接写 SQL 逻辑
# 数据库操作封装成独立函数，放在 crud.py 或对应模块中
```

- 数据库操作函数统一放在 `crud.py` 中
- 每个请求结束后必须关闭 session（使用 `Depends(get_db)` 自动管理）
- 不要在循环中执行数据库查询（N+1 问题）

### 2.6 安全规则

```python
# ✅ 密码处理
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

- 密码必须使用 bcrypt 哈希，**禁止明文存储**
- JWT secret 从环境变量读取，**禁止硬编码**
- 文件上传必须校验内容（不信任文件扩展名），只接受合法 JSON
- 所有数据库查询使用 ORM 参数化，**禁止字符串拼接 SQL**

### 2.7 配置管理

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    jwt_secret: str          # 从环境变量 JWT_SECRET 读取
    jwt_expire_hours: int = 8
    gaokao_near_gap: int = 10   # 高考接近线容差
    xuekao_near_gap: int = 5    # 学考接近线容差
    data_dir: str = "data/schools"

    class Config:
        env_file = ".env"

settings = Settings()
```

- 所有可配置项放在 `config.py`，不要散落在各个文件中
- 敏感配置（JWT secret、数据库路径）通过 `.env` 文件注入
- `.env` 文件加入 `.gitignore`，仓库中只提供 `.env.example`

---

## 三、前端规范（Vue 3）

### 3.1 组件规范

```vue
<!-- ✅ 正确：使用 <script setup>，明确 props 和 emits -->
<script setup>
/**
 * ResultCard.vue — 单条匹配结果展示卡片
 */
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['download'])

// 状态颜色映射
const statusColor = computed(() => {
  const map = { '达线': 'success', '接近': 'warning', '不达标': 'danger' }
  return map[props.result.status] || 'info'
})
</script>
```

- 所有组件使用 `<script setup>` 语法
- 所有 `props` 必须定义类型和 required
- 组件顶部写明用途注释
- 组件名使用 PascalCase，文件名与组件名一致

### 3.2 API 请求规范

```javascript
// api/index.js — Axios 实例配置
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截：自动注入 JWT
request.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截：统一处理错误码
request.interceptors.response.use(
  response => {
    const { code, msg, data } = response.data
    if (code === 0) return data
    if (code === 4010) {
      // Token 过期，跳转登录
      useAuthStore().logout()
      router.push('/login')
    }
    return Promise.reject(new Error(msg))
  },
  error => Promise.reject(error)
)

export default request
```

- **所有接口调用**通过统一的 `request` 实例，不要直接使用 `axios`
- 按模块拆分 API 函数，如 `api/auth.js`、`api/match.js`、`api/admin.js`

```javascript
// api/auth.js
import request from './index'

export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')
```

### 3.3 Pinia Store 规范

```javascript
// stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')
  const isAdmin = computed(() => ['super_admin', 'admin'].includes(user.value?.role))

  async function login(username, password) {
    const data = await loginApi({ username, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, isSuperAdmin, isAdmin, login, logout }
})
```

- Store 使用 Composition API 风格（`defineStore` + setup 函数）
- 计算属性封装角色判断逻辑，**组件中不要直接判断 role 字符串**

### 3.4 路由守卫规范

```javascript
// router/index.js
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  // 未登录跳登录页
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return next('/login')
  }

  // 角色不足静默降级
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next('/match')
  }

  if (to.meta.requiresSuper && !auth.isSuperAdmin) {
    return next('/match')
  }

  next()
})
```

路由 meta 定义：
```javascript
{ path: '/match',        meta: { requiresAuth: true } }
{ path: '/admin/users',  meta: { requiresAuth: true, requiresAdmin: true } }
{ path: '/super/data',   meta: { requiresAuth: true, requiresSuper: true } }
```

### 3.5 表单规范

```vue
<!-- ✅ 使用 Element Plus 表单校验 -->
<el-form :model="form" :rules="rules" ref="formRef">
  <el-form-item label="高考成绩" prop="gaokaoScore">
    <el-input-number v-model="form.gaokaoScore" :min="0" :max="750" />
  </el-form-item>
</el-form>

<script setup>
const rules = {
  gaokaoScore: [
    { required: true, message: '请输入高考成绩', trigger: 'blur' },
    { type: 'number', min: 0, max: 750, message: '分数范围 0-750', trigger: 'blur' }
  ]
}
</script>
```

- 所有表单使用 Element Plus `el-form` + `rules` 校验
- 提交前调用 `formRef.value.validate()` 校验
- 学考等级下拉选项固定为 `['A', 'B', 'C', 'D', 'E']`，不可自定义

### 3.6 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `ResultCard.vue` |
| 视图文件 | PascalCase + View | `MatchView.vue` |
| Store 文件 | camelCase | `auth.js` |
| API 文件 | camelCase | `match.js` |
| 变量 / 函数 | camelCase | `gaokaoScore`, `handleSubmit` |
| CSS 类名 | kebab-case | `.result-card` |
| 常量 | UPPER_SNAKE_CASE | `GRADE_OPTIONS` |

---

## 四、安全规范

### 4.1 前端
- **不要在前端做权限判断来隐藏数据**，前端只做 UI 隐藏，真正的权限校验在后端
- 不要在 `console.log` 中打印 token 或用户敏感信息
- 不要在 URL 中传递 token（只用 Header）

### 4.2 后端
- 每个需要权限的接口都必须有对应的 `Depends(require_xxx)` 装饰
- 修改他人数据前，必须先校验操作者角色是否有权限
- 文件上传接口：先校验 → 再写入，校验失败不产生任何文件

### 4.3 数据隔离
- admin 查询用户列表时，SQL 必须过滤掉 `role = 'super_admin'` 的账号
- 任何接口返回的用户对象，都必须使用 `UserResponse` schema，确保 password 字段不被序列化

---

## 五、Git 提交规范

```
feat: 新增账号管理接口
fix: 修复学考赋值分计算错误
refactor: 重构路由守卫逻辑
docs: 更新 AGENT.md 目录结构
chore: 添加 .env.example 文件
```

格式：`类型: 简短描述（中文）`

| 类型 | 含义 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| refactor | 重构（不改变功能） |
| docs | 文档更新 |
| chore | 配置/依赖/构建 |
| test | 测试相关 |

---

## 六、禁止事项清单

```
❌ 禁止在任何接口响应中包含 password 字段
❌ 禁止硬编码 JWT secret、数据库路径等敏感配置
❌ 禁止在前端组件中直接判断 role 字符串（用 store 的计算属性）
❌ 禁止修改 matcher.py（已测试通过的核心逻辑）
❌ 禁止上传文件后跳过校验直接写入
❌ 禁止在循环中执行数据库查询
❌ 禁止在组件中直接调用 axios（必须通过 api/ 模块）
❌ 禁止使用 Options API（统一使用 Composition API + script setup）
❌ 禁止省略 props 的类型定义
❌ 禁止在 .env 文件中提交真实密钥到 git
```
