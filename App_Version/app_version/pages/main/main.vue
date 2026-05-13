<template>
  <view class="page">
    <view class="card status-card">
      <view class="row">
        <text class="label">登录状态</text>
        <text :class="isLoggedIn ? 'ok' : 'bad'">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
      </view>
      <view class="row small" v-if="isLoggedIn">
        <text>login_name: {{ form.loginName }}</text>
      </view>
      <button class="btn btn-danger" @click="logout" :disabled="running">退出登录</button>
    </view>

    <view class="card">
      <view class="title">配置参数</view>

      <view class="field">
        <text class="label">LOGIN_NAME / USER_ID</text>
        <input v-model="form.loginName" class="input" placeholder="请输入 LOGIN_NAME / USER_ID" />
      </view>

      <view class="field">
        <text class="label">SES_ID</text>
        <input v-model="form.sesId" class="input" placeholder="请输入 SES_ID" />
      </view>

      <view class="field">
        <text class="label">EXCHANGE_ID（9=2块 / 10=4块 / 11=6块）</text>
        <input v-model="form.exchangeId" class="input" placeholder="例如 9 / 10 / 11" />
      </view>

      <view class="field">
        <text class="label">抢票时间</text>
        <input v-model="form.runTime" class="input" placeholder="YYYY-MM-DD HH:MM:SS" />
      </view>

      <view class="field inline">
        <view class="half">
          <text class="label">运行次数</text>
          <input v-model="form.runCount" class="input" placeholder="请输入运行次数" />
        </view>
        <view class="half">
          <text class="label">运行间隔(秒)</text>
          <input v-model="form.timeSleep" class="input" placeholder="请输入运行间隔" />
        </view>
      </view>

      <view class="actions">
        <button class="btn btn-primary" @click="startProgram" :disabled="running || !isLoggedIn">启动</button>
        <button class="btn btn-danger" @click="stopProgram" :disabled="!running">停止</button>
        <button class="btn" @click="runDailyTask" :disabled="running || dailyTaskRunning || !isLoggedIn">
          {{ dailyTaskRunning ? '执行中...' : '执行每日任务' }}
        </button>
      </view>
    </view>

    <view class="card">
      <view class="title">运行日志</view>
      <scroll-view scroll-y class="log-box">
        <view class="log-line" v-for="(item, idx) in logs" :key="idx">{{ item }}</view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { runDailyTaskWorkflow, runExchangeOnce } from '../../src/services/taskService'
import { clearAuth, loadAuth, loadConfig, saveAuth, saveConfig } from '../../src/utils/storage'
import { formatDateTime, getNextRunTime, parseDateTime } from '../../src/utils/time'

// ==================== 状态 ====================
const running = ref(false)
const dailyTaskRunning = ref(false)
const stopRequested = ref(false)
const timerId = ref(null)
const logs = ref([])
const form = reactive({
  loginName: '',
  userId: '',
  sesId: '',
  exchangeId: '10',
  runTime: getNextRunTime(),
  runCount: '100',
  timeSleep: '0.08'
})

const isLoggedIn = computed(() => Boolean(form.loginName && form.sesId))

// ==================== 方法 ====================
function persistConfig() {
  saveConfig({ ...form })
}

function appendLog(message) {
  const ts = formatDateTime(new Date())
  logs.value.push(`[${ts}] ${message}`)
}

function logout() {
  if (running.value || dailyTaskRunning.value) {
    uni.showToast({ title: '请先停止任务后再退出登录', icon: 'none' })
    return
  }

  clearAuth()
  saveAuth({ isLoggedIn: false })
  appendLog('已退出登录')
  uni.redirectTo({ url: '/pages/login/login' })
}

function validateInputs() {
  const { loginName, sesId, exchangeId, runTime, runCount, timeSleep } = form
  if (!loginName || !sesId || !exchangeId || !runTime || !runCount || !timeSleep) {
    throw new Error('所有字段都必须填写')
  }

  const countNum = Number(runCount)
  const sleepNum = Number(timeSleep)
  if (!Number.isFinite(countNum) || countNum <= 0) {
    throw new Error('运行次数必须是正数')
  }
  if (!Number.isFinite(sleepNum) || sleepNum <= 0) {
    throw new Error('运行间隔必须是正数')
  }

  const runDate = parseDateTime(runTime)
  return { runCount: countNum, timeSleep: sleepNum, runDate }
}

function stopProgram() {
  stopRequested.value = true
  running.value = false
  if (timerId.value) {
    clearTimeout(timerId.value)
    timerId.value = null
  }
  appendLog('程序已停止')
}

async function startProgram() {
  try {
    persistConfig()
    const { runCount, timeSleep, runDate } = validateInputs()
    const now = new Date()

    stopRequested.value = false
    running.value = true
    appendLog(`程序已启动，将在 ${form.runTime} 执行兑换任务，共执行 ${runCount} 次`)

    const waitMs = Math.max(runDate.getTime() - now.getTime(), 0)
    timerId.value = setTimeout(async () => {
      for (let i = 0; i < runCount; i += 1) {
        if (stopRequested.value) break
        appendLog(`准备执行第 ${i + 1} 次兑换请求`)
        try {
          await runExchangeOnce({
            loginName: form.loginName,
            userId: form.userId || form.loginName,
            sesId: form.sesId,
            exchangeId: form.exchangeId,
            log: appendLog
          })
        } catch (error) {
          appendLog(`兑换请求失败: ${error.message}`)
        }

        if (i < runCount - 1 && !stopRequested.value) {
          await new Promise((resolve) => {
            timerId.value = setTimeout(resolve, Math.max(timeSleep * 1000, 20))
          })
        }
      }

      running.value = false
      if (!stopRequested.value) {
        appendLog('程序执行完成')
      }
      timerId.value = null
    }, waitMs)
  } catch (error) {
    running.value = false
    uni.showToast({ title: error.message, icon: 'none' })
  }
}

async function runDailyTask() {
  if (!form.loginName || !form.sesId) {
    uni.showToast({ title: 'LOGIN_NAME 和 SES_ID 必须填写', icon: 'none' })
    return
  }

  persistConfig()
  dailyTaskRunning.value = true
  appendLog('开始执行每日任务工作流')
  try {
    await runDailyTaskWorkflow({
      loginName: form.loginName,
      sesId: form.sesId,
      log: appendLog
    })
    appendLog('每日任务执行完成')
  } catch (error) {
    appendLog(`每日任务执行失败: ${error.message}`)
  } finally {
    dailyTaskRunning.value = false
  }
}

// ==================== 生命周期 ====================
onLoad(() => {
  const auth = loadAuth()
  const config = loadConfig()

  if (!auth || !auth.isLoggedIn || !auth.loginName || !auth.sesId) {
    uni.redirectTo({ url: '/pages/login/login' })
    return
  }

  form.loginName = auth.loginName
  form.userId = auth.userId || auth.loginName
  form.sesId = auth.sesId

  form.exchangeId = config.exchangeId || form.exchangeId
  form.runTime = config.runTime || form.runTime
  form.runCount = config.runCount || form.runCount
  form.timeSleep = config.timeSleep || form.timeSleep

  appendLog('登录状态已恢复')
  persistConfig()
})

// ==================== 监听 ====================
watch(form, () => { persistConfig() }, { deep: true })
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20rpx;
  box-sizing: border-box;
}

.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
}

.status-card .row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.status-card .small {
  font-size: 24rpx;
  color: #6e6e73;
}

.ok {
  color: #1f9d55;
  font-weight: 700;
}

.bad {
  color: #d93025;
  font-weight: 700;
}

.title {
  font-size: 34rpx;
  font-weight: 700;
  margin-bottom: 22rpx;
}

.field {
  margin-bottom: 18rpx;
}

.inline {
  display: flex;
  gap: 14rpx;
}

.half {
  flex: 1;
}

.label {
  display: block;
  margin-bottom: 8rpx;
  color: #6e6e73;
}

.input {
  width: 100%;
  height: 78rpx;
  border: 1rpx solid #d2d2d7;
  border-radius: 14rpx;
  padding: 0 16rpx;
  box-sizing: border-box;
}

.actions {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.btn {
  border-radius: 14rpx;
  font-size: 26rpx;
  height: 76rpx;
  padding: 0 20rpx;
}

.btn-primary {
  background: #007aff;
  color: #fff;
}

.btn-danger {
  background: #fff5f4;
  color: #ff3b30;
}

.log-box {
  height: 360rpx;
  border: 1rpx solid #e5e5ea;
  border-radius: 12rpx;
  padding: 12rpx;
  box-sizing: border-box;
  background: #fbfbfd;
}

.log-line {
  font-size: 24rpx;
  line-height: 1.6;
  margin-bottom: 6rpx;
  word-break: break-all;
}
</style>
