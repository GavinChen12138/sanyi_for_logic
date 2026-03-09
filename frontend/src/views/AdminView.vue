<script setup>
/**
 * AdminView.vue — 账号管理页面（admin 和 super_admin 可用）
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
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
    Message.error(err.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreateUser() {
  await createFormRef.value.validate()
  try {
    await createUser(createForm)
    Message.success('账号创建成功')
    showCreateDialog.value = false
    Object.assign(createForm, { username: '', password: '', name: '', role: 'planner' })
    await fetchUsers()
  } catch (err) {
    Message.error(err.message || '创建失败')
  }
}

async function handleResetPassword(user) {
  try {
    Modal.prompt({
      title: `重置 ${user.name} 的密码`,
      content: '请输入新密码',
      onOk: async (value) => {
        if (!value || value.length < 4) {
          Message.error('密码长度不能少于4位')
          return Promise.reject()
        }
        await resetPassword(user.id, { new_password: value })
        Message.success('密码重置成功')
      }
    })
  } catch { /* ignored */ }
}

async function handleChangeRole(user, newRole) {
  try {
    await changeRole(user.id, { new_role: newRole })
    Message.success('角色修改成功')
    await fetchUsers()
  } catch (err) {
    Message.error(err.message || '修改失败')
    await fetchUsers()
  }
}

async function handleToggleStatus(user) {
  const newStatus = !user.is_active
  const action = newStatus ? '启用' : '禁用'
  try {
    Modal.confirm({
      title: '确认操作',
      content: `确定${action}账号 "${user.name}" 吗？`,
      onOk: async () => {
        await changeStatus(user.id, { is_active: newStatus })
        Message.success(`账号已${action}`)
        await fetchUsers()
      }
    })
  } catch { /* ignored */ }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="page-container">
    <a-card class="admin-card" hoverable>
      <template #title>
        <div class="card-header">
          <span>👥 账号管理</span>
          <a-button type="primary" @click="showCreateDialog = true">
            <template #icon><icon-plus /></template>
            创建账号
          </a-button>
        </div>
      </template>

      <a-table :data="users" :loading="loading" :stripe="true">
        <template #columns>
          <a-table-column data-index="name" title="姓名" :width="100" />
          <a-table-column data-index="username" title="用户名" :width="120" />
          <a-table-column title="角色" :width="140">
            <template #cell="{ record }">
              <a-select
                :model-value="record.role"
                size="small"
                :disabled="record.id === auth.user?.id"
                @change="(val) => handleChangeRole(record, val)"
              >
                <a-option
                  v-for="opt in (auth.isSuperAdmin ? ROLE_OPTIONS_FOR_SUPER : ROLE_OPTIONS_FOR_ADMIN)"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </a-select>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="80" align="center">
            <template #cell="{ record }">
              <a-tag :color="record.is_active ? 'green' : 'red'" size="small">
                {{ record.is_active ? '正常' : '禁用' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="创建时间" :width="160">
            <template #cell="{ record }">
              {{ new Date(record.created_at).toLocaleString('zh-CN') }}
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="180" fixed="right">
            <template #cell="{ record }">
              <a-button
                type="text"
                size="small"
                :disabled="record.id === auth.user?.id"
                @click="handleResetPassword(record)"
              >
                重置密码
              </a-button>
              <a-button
                type="text"
                :status="record.is_active ? 'danger' : 'success'"
                size="small"
                :disabled="record.id === auth.user?.id"
                @click="handleToggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 创建账号弹窗 -->
    <a-modal v-model:visible="showCreateDialog" title="创建账号" :width="460" unmount-on-close @cancel="showCreateDialog = false" @ok="handleCreateUser">
      <a-form ref="createFormRef" :model="createForm" :rules="createRules" auto-label-width>
        <a-form-item label="姓名" field="name">
          <a-input v-model="createForm.name" placeholder="请输入姓名" />
        </a-form-item>
        <a-form-item label="用户名" field="username">
          <a-input v-model="createForm.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="初始密码" field="password">
          <a-input-password v-model="createForm.password" placeholder="请输入初始密码" />
        </a-form-item>
        <a-form-item label="角色" field="role">
          <a-select v-model="createForm.role">
            <a-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
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
