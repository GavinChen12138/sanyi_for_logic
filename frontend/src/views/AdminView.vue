<script setup>
/**
 * AdminView.vue — 账号管理页面（admin 和 super_admin 可用）
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getUsers, createUser, resetPassword, changeRole, changeStatus } from '@/api/admin'
import { ROLE_LABEL_MAP, ROLE_OPTIONS_FOR_ADMIN, ROLE_OPTIONS_FOR_SUPER } from '@/constants'

const auth = useAuthStore()
const users = ref([])
const loading = ref(false)

// 创建账号弹窗
const showCreateDialog = ref(false)
const createForm = reactive({ username: '', password: '', name: '', role: 'planner' })
const createFormRef = ref(null)

const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 4, message: '密码长度不能少于4位', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

// 角色选项（根据当前用户身份）
const roleOptions = computed(() => {
  return auth.isSuperAdmin ? ROLE_OPTIONS_FOR_SUPER : ROLE_OPTIONS_FOR_ADMIN
})

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (err) {
    ElMessage.error(err.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreateUser() {
  await createFormRef.value.validate()
  try {
    await createUser(createForm)
    ElMessage.success('账号创建成功')
    showCreateDialog.value = false
    Object.assign(createForm, { username: '', password: '', name: '', role: 'planner' })
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  }
}

async function handleResetPassword(user) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新密码', `重置 ${user.name} 的密码`, {
      inputPattern: /.{4,}/,
      inputErrorMessage: '密码长度不能少于4位'
    })
    await resetPassword(user.id, { new_password: value })
    ElMessage.success('密码重置成功')
  } catch { /* 用户取消 */ }
}

async function handleChangeRole(user, newRole) {
  try {
    await changeRole(user.id, { new_role: newRole })
    ElMessage.success('角色修改成功')
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.message || '修改失败')
    await fetchUsers()
  }
}

async function handleToggleStatus(user) {
  const newStatus = !user.is_active
  const action = newStatus ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定${action}账号 "${user.name}" 吗？`, '确认操作')
    await changeStatus(user.id, { is_active: newStatus })
    ElMessage.success(`账号已${action}`)
    await fetchUsers()
  } catch { /* 用户取消 */ }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="page-container">
    <el-card shadow="hover" class="admin-card">
      <template #header>
        <div class="card-header">
          <span>👥 账号管理</span>
          <el-button type="primary" @click="showCreateDialog = true" :icon="'Plus'">
            创建账号
          </el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column label="角色" min-width="140">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              size="small"
              :disabled="row.id === auth.user?.id"
              @change="(val) => handleChangeRole(row, val)"
            >
              <el-option
                v-for="opt in (auth.isSuperAdmin ? ROLE_OPTIONS_FOR_SUPER : ROLE_OPTIONS_FOR_ADMIN)"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              text
              type="primary"
              size="small"
              :disabled="row.id === auth.user?.id"
              @click="handleResetPassword(row)"
            >
              重置密码
            </el-button>
            <el-button
              text
              :type="row.is_active ? 'danger' : 'success'"
              size="small"
              :disabled="row.id === auth.user?.id"
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建账号弹窗 -->
    <el-dialog v-model="showCreateDialog" title="创建账号" width="460px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="请输入初始密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser">确定创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}
</style>
