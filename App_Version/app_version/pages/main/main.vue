<template>
  <view class="page">
    <!-- 顶部横幅图片 -->
    <view class="hero">
      <image class="hero-image" src="../../resouse/home.jpg" mode="widthFix" />
    </view>

    <!-- 登录状态卡片 -->
    <view class="card status-card">
      <view class="row">
        <text class="label">登录状态</text>
        <text :class="isLoggedIn ? 'ok' : 'bad'">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
      </view>
      <view class="row small" v-if="userName">
        <text>当前用户: {{ userName }}</text>
        <text v-if="remainIntegral > 0" style="color:#1f9d55;">积分: {{ remainIntegral }}</text>
      </view>
      <view class="row small" v-if="isLoggedIn">
        <text>login_name: {{ form.loginName }}</text>
      </view>
      <button class="btn btn-danger" @click="logout" :disabled="running">退出登录</button>
    </view>

    <!-- 配置参数卡片 -->
    <view class="card">
      <view class="title">配置参数</view>

      <!-- LOGIN_NAME 输入框 -->
      <view class="field">
        <text class="label">LOGIN_NAME / USER_ID</text>
        <input v-model="form.loginName" class="input" placeholder="请输入 LOGIN_NAME / USER_ID" />
      </view>

      <!-- SES_ID 输入框 -->
      <view class="field">
        <text class="label">SES_ID</text>
        <input v-model="form.sesId" class="input" placeholder="请输入 SES_ID" />
      </view>

      <!-- 兑换面额选择 -->
      <view class="field">
        <text class="label">EXCHANGE_ID（9=2块 / 10=4块 / 11=6块）</text>
        <input v-model="form.exchangeId" class="input" placeholder="例如 9 / 10 / 11" />
      </view>

      <!-- 定时抢票时间设置 -->
      <view class="field">
        <text class="label">抢票时间</text>
        <input v-model="form.runTime" class="input" placeholder="YYYY-MM-DD HH:MM:SS" />
      </view>

      <!-- 运行次数与间隔（并列布局） -->
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

      <!-- 操作按钮组 -->
      <view class="actions">
        <view class="action-row">
          <button class="btn btn-primary flex-1" @click="startProgram" :disabled="running || !isLoggedIn">启动</button>
          <button class="btn btn-stop flex-1" @click="stopProgram" :disabled="!running">停止</button>
        </view>
        <view class="action-row">
          <button class="btn flex-1" @click="runDailyTask" :disabled="running || dailyTaskRunning || !isLoggedIn">
            {{ dailyTaskRunning ? '执行中...' : '执行每日任务' }}
          </button>
          <button class="btn btn-qr flex-1" @click="goQrCode" :disabled="!isLoggedIn">绿色出行码</button>
        </view>
        <view class="action-row">
          <button class="btn btn-github full" @click="openGithub">GitHub</button>
        </view>
      </view>
    </view>

    <!-- 运行日志面板 -->
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
import { queryUserInfo } from '../../src/services/authService'

// ==================== 响应式状态定义 ====================
/** 是否正在执行兑换任务循环 */
const running = ref(false)
/** 当前登录用户姓名 */
const userName = ref('')
/** 当前剩余积分 */
const remainIntegral = ref(0)
/** 是否正在执行每日任务 */
const dailyTaskRunning = ref(false)
/** 是否请求停止兑换任务 */
const stopRequested = ref(false)
/** 定时器句柄（用于 setTimeout 取消） */
const timerId = ref(null)
/** 运行日志列表，每项为一行日志文本 */
const logs = ref([])
/** 配置表单数据 */
const form = reactive({
  loginName: '',   // 用户登录名
  userId: '',      // 用户 ID
  sesId: '',       // 会话 ID
  exchangeId: '10', // 兑换面额 ID
  runTime: getNextRunTime(), // 定时执行时间
  runCount: '10',          // 重复执行次数
  timeSleep: '0.3'         // 每次执行间隔（秒）
})

/** 计算属性：是否已登录（loginName 和 sesId 均不为空） */
const isLoggedIn = computed(() => Boolean(form.loginName && form.sesId))

// ==================== 方法 ====================
/** 将当前表单配置持久化到本地存储 */
function persistConfig() {
  saveConfig({ ...form })
}

/**
 * 追加一条日志记录（带时间戳）
 * @param {string} message - 日志内容
 */
function appendLog(message) {
  const ts = formatDateTime(new Date())
  logs.value.push(`[${ts}] ${message}`)
}

/**
 * 退出登录：清除本地登录态，跳转回登录页
 */
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

/**
 * 校验用户输入的配置参数是否合法
 * @returns {{ runCount: number, timeSleep: number, runDate: Date }} 解析后的数值
 * @throws {Error} 校验失败时抛出异常
 */
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

/**
 * 停止兑换任务：设置停止标志，清除定时器
 */
function stopProgram() {
  stopRequested.value = true
  running.value = false
  if (timerId.value) {
    clearTimeout(timerId.value)
    timerId.value = null
  }
  appendLog('程序已停止')
}

/**
 * 启动兑换任务：保存配置，校验参数，
 * 等待到指定时间后开始循环执行兑换请求，每次执行间隔由 timeSleep 控制
 */
async function startProgram() {
  try {
    persistConfig()
    const { runCount, timeSleep, runDate } = validateInputs()
    const now = new Date()

    stopRequested.value = false
    running.value = true
    appendLog(`程序已启动，将在 ${form.runTime} 执行兑换任务，共执行 ${runCount} 次`)

    // 计算距离开抢时间的等待毫秒数
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

        // 非最后一次执行且未停止时，按间隔等待
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

/** 跳转到绿色出行二维码页面 */
function goQrCode() {
  uni.navigateTo({ url: '/pages/qrcode/qrcode' })
}

/** 打开 GitHub 仓库 */
function openGithub() {
  uni.setClipboardData({
    data: 'https://github.com/BAOfanTing/AutoTicket',
    success: () => {
      uni.showToast({ title: 'GitHub 链接已复制', icon: 'none' })
    }
  })
}

/**
 * 执行每日任务工作流
 */
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
/**
 * 页面加载时：从本地存储恢复登录态和配置，
 * 如果未登录则重定向到登录页
 */
onLoad(async () => {
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
  form.runCount = config.runCount || form.runCount
  form.timeSleep = config.timeSleep || form.timeSleep

  // 调用 U005 验证 ses_id 是否仍然有效，同时获取用户姓名
  const userInfo = await queryUserInfo(form.loginName, form.sesId)
  if (!userInfo) {
    appendLog('登录会话已失效，请重新登录')
    clearAuth()
    saveAuth({ isLoggedIn: false })
    uni.showModal({
      title: '登录已失效',
      content: '登录会话已失效，请重新登录。',
      showCancel: false,
      success() {
        uni.redirectTo({ url: '/pages/login/login' })
      }
    })
    return
  }

  userName.value = userInfo.name || userInfo.sensitive_name || ''
  remainIntegral.value = parseInt(userInfo.remain_integral) || 0
  if (userName.value) {
    appendLog(`欢迎, ${userName.value}  当前积分: ${remainIntegral.value}`)
  }

  appendLog('登录状态已恢复')
  persistConfig()
})

// ==================== 监听 ====================
/** 表单数据变化时自动持久化保存到本地存储 */
watch(form, () => { persistConfig() }, { deep: true })
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20rpx;
  box-sizing: border-box;
}

.hero {
  margin-bottom: 20rpx;
}

.hero-image {
  display: block;
  width: 100%;
  border-radius: 20rpx;
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
  flex-direction: column;
  gap: 12rpx;
}

.action-row {
  display: flex;
  gap: 12rpx;
}

.flex-1 {
  flex: 1;
}

.full {
  width: 100%;
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

.btn-stop {
  background: #ff3b30;
  color: #fff;
}

.btn-qr {
  background: #1f9d55;
  color: #fff;
}

.btn-github {
  background: #333;
  color: #fff;
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
