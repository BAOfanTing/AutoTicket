<template>
  <view class="page">
    <!-- 顶部横幅图片 -->
    <view class="hero">
      <image class="hero-image" src="../../resouse/home.jpg" mode="widthFix" />
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">仅供学习使用</view>

    <!-- 登录状态卡片（Material 用户资料头） -->
    <view class="card status-card">
      <view class="status-head">
        <view class="status-avatar">
          <text class="status-avatar-text">{{ (userName || '用户').slice(0, 1) }}</text>
        </view>
        <view class="status-meta">
          <view class="status-user">
            <text class="status-name">{{ userName || '未登录' }}</text>
            <text class="chip" :class="isLoggedIn ? 'chip-ok' : 'chip-bad'">{{ isLoggedIn ? '已登录' : '未登录' }}</text>
          </view>
          <text v-if="remainIntegral > 0" class="status-integral">积分 · {{ remainIntegral }}</text>
        </view>
      </view>
      <button class="btn btn-outline-danger" @click="logout" :disabled="running">退出登录</button>
    </view>

    <!-- 配置参数卡片 -->
    <view class="card">
      <view class="card-head">
        <text class="title">配置参数</text>
      </view>

      <!-- 兑换面额选择 -->
      <view class="field">
        <text class="label">优惠券面额</text>
        <picker mode="selector" :range="exchangeOptions" range-key="label" :value="exchangeIndex" @change="onExchangeChange">
          <view class="input picker">
            <text class="input-value">{{ exchangeOptions[exchangeIndex].label }}</text>
            <text class="picker-arrow">▾</text>
          </view>
        </picker>
      </view>

      <!-- 定时抢票时间设置 -->
      <view class="field">
        <text class="label">抢票时间</text>
        <input v-model="form.runTime" class="input" placeholder="YYYY-MM-DD HH:MM:SS" placeholder-style="color:#5f6368;" />
      </view>

      <!-- 运行次数与间隔（并列布局） -->
      <view class="field inline">
        <view class="half">
          <text class="label">运行次数</text>
          <input v-model="form.runCount" class="input" placeholder="次数" placeholder-style="color:#5f6368;" />
        </view>
        <view class="half">
          <text class="label">运行间隔(秒)</text>
          <input v-model="form.timeSleep" class="input" placeholder="间隔" placeholder-style="color:#5f6368;" />
        </view>
      </view>

      <!-- 操作按钮组 -->
      <view class="actions">
        <view class="action-row">
          <button class="btn btn-primary flex-1" @click="startProgram" :disabled="running || !isLoggedIn">启动</button>
          <button class="btn btn-fill-error flex-1" @click="stopProgram" :disabled="!running">停止</button>
        </view>
        <view class="action-row">
          <button class="btn btn-outline flex-1" @click="runDailyTask" :disabled="running || dailyTaskRunning || !isLoggedIn">
            {{ dailyTaskRunning ? '执行中...' : '执行每日任务' }}
          </button>
          <button class="btn btn-success flex-1" @click="goQrCode" :disabled="!isLoggedIn">绿色出行码</button>
        </view>
        <!-- 每日任务完成状态标签 -->
        <view class="daily-status" v-if="dailyTaskDone">
          <text class="daily-status-chip">✓ 每日任务已完成</text>
        </view>
      </view>
    </view>

    <!-- 实时统计卡片 -->
    <view class="card">
      <view class="card-head">
        <text class="title">实时统计</text>
      </view>
      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-label">在线人数</text>
          <text class="stat-value" style="color:#1e8e3e;">{{ statsOnline }}</text>
        </view>
        <view class="stat-card">
          <text class="stat-label">2元券</text>
          <text class="stat-value">{{ statsType9 }}</text>
        </view>
        <view class="stat-card">
          <text class="stat-label">4元券</text>
          <text class="stat-value">{{ statsType10 }}</text>
        </view>
        <view class="stat-card">
          <text class="stat-label">6元券</text>
          <text class="stat-value">{{ statsType11 }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="card-head">
        <text class="title">运行日志</text>
      </view>
      <scroll-view scroll-y class="log-box">
        <view class="log-line" v-for="(item, idx) in logs" :key="idx">{{ item }}</view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import { runDailyTaskWorkflow, runExchangeOnce } from '../../src/services/taskService'
import { clearAuth, loadAuth, loadConfig, saveAuth, saveConfig } from '../../src/utils/storage'
import { formatDateTime, getNextRunTime, parseDateTime } from '../../src/utils/time'
import { queryUserInfo, syncServerTime } from '../../src/services/authService'
import { isStatsEnabled, fetchStats, reportOnline, reportOffline } from '../../src/services/statsService'

// ==================== 响应式状态定义 ====================
/** 是否正在执行兑换任务循环 */
const running = ref(false)
/** 当前登录用户姓名 */
const userName = ref('')
/** 当前剩余积分 */
const remainIntegral = ref(0)
/** 是否正在执行每日任务 */
const dailyTaskRunning = ref(false)
/** 每日任务是否已完成 */
const dailyTaskDone = ref(false)
/** 每日任务完成日期（当天有效） */
const dailyTaskDoneDate = ref('')
/** 是否请求停止兑换任务 */
const stopRequested = ref(false)
/** 定时器句柄（用于 setTimeout 取消） */
const timerId = ref(null)
/** 运行日志列表，每项为一行日志文本 */
const logs = ref([])

// ==================== 实时统计 ====================
/** 统计面板是否启用 */
const statsEnabled = isStatsEnabled()
/** 在线人数 */
const statsOnline = ref(0)
/** 2元券抢到数 */
const statsType9 = ref(0)
/** 4元券抢到数 */
const statsType10 = ref(0)
/** 6元券抢到数 */
const statsType11 = ref(0)
/** 统计轮询定时器 */
let statsTimer = null
/** 优惠券面额选项 */
const exchangeOptions = [
  { label: '2元优惠券', value: '9' },
  { label: '4元优惠券', value: '10' },
  { label: '6元优惠券', value: '11' }
]
/** 当前选中的优惠券面额索引 */
const exchangeIndex = ref(1)
/** 配置表单数据 */
const form = reactive({
  loginName: '',   // 用户登录名
  userId: '',      // 用户 ID
  sesId: '',       // 会话 ID
  exchangeId: '10', // 兑换面额 ID
  runTime: getNextRunTime(), // 定时执行时间
  runCount: '10',          // 重复执行次数
  timeSleep: '0.2'         // 每次执行间隔（秒）
})

/** 计算属性：是否已登录（loginName 和 sesId 均不为空） */
const isLoggedIn = computed(() => Boolean(form.loginName && form.sesId))

// ==================== 方法 ====================
/** 优惠券面额切换 */
function onExchangeChange(e) {
  exchangeIndex.value = e.detail.value
  form.exchangeId = exchangeOptions[exchangeIndex.value].value
}

/** 将当前表单配置持久化到本地存储 */
function persistConfig() {
  saveConfig({ ...form, dailyTaskDoneDate: dailyTaskDoneDate.value })
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
  dailyTaskDone.value = false
  dailyTaskDoneDate.value = ''
  stopStatsPolling()
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
  if (!Number.isFinite(countNum) || countNum <= 0 || countNum > 20) {
    throw new Error('运行次数必须是 1~20 之间的正整数')
  }
  if (!Number.isFinite(sleepNum) || sleepNum < 0.15) {
    throw new Error('运行间隔不能小于 0.15 秒')
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

    stopRequested.value = false
    running.value = true
    appendLog('正在同步服务器时间...')

    let offset = 0
    try {
      const serverTime = await syncServerTime(form.loginName, form.sesId)
      offset = serverTime - Date.now()
      appendLog(`服务器时间同步完成，本地偏移: ${offset > 0 ? '+' : ''}${offset}ms`)
    } catch (error) {
      appendLog(`服务器时间同步失败，使用本地时间: ${error.message}`)
    }

    appendLog(`程序已启动，将在 ${form.runTime} 执行兑换任务，共执行 ${runCount} 次`)

    // 基于服务器时间计算等待毫秒数
    const waitMs = Math.max(runDate.getTime() - (Date.now() + offset), 0)
    timerId.value = setTimeout(async () => {
      for (let i = 0; i < runCount; i += 1) {
        if (stopRequested.value) break
        appendLog(`准备执行第 ${i + 1} 次兑换请求`)
        // 不等待请求响应，直接连续发起（与 Python 版行为一致）
        runExchangeOnce({
          loginName: form.loginName,
          userId: form.userId || form.loginName,
          sesId: form.sesId,
          exchangeId: form.exchangeId,
          log: appendLog
        }).catch((error) => {
          appendLog(`兑换请求失败: ${error.message}`)
        })

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

// ==================== 实时统计 ====================
/** 拉取一次统计数据并刷新界面 */
async function fetchAndShowStats() {
  try {
    const data = await fetchStats()
    if (data) {
      statsOnline.value = data.online
      statsType9.value = data.by_type['9'] || 0
      statsType10.value = data.by_type['10'] || 0
      statsType11.value = data.by_type['11'] || 0
    }
  } catch {
    // 静默失败
  }
}

/** 启动统计轮询（每 60 秒刷新一次） */
function startStatsPolling() {
  if (!statsEnabled) return
  reportOnline('open')
  fetchAndShowStats()
  statsTimer = setInterval(fetchAndShowStats, 60000)
}

/** 停止统计轮询 */
function stopStatsPolling() {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
  reportOffline()
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
  dailyTaskDone.value = false
  appendLog('开始执行每日任务工作流')
  try {
    await runDailyTaskWorkflow({
      loginName: form.loginName,
      sesId: form.sesId,
      log: appendLog
    })
    dailyTaskDone.value = true
    dailyTaskDoneDate.value = new Date().toISOString().slice(0, 10)
    persistConfig()
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

  const savedExchangeId = config.exchangeId || form.exchangeId
  const foundIndex = exchangeOptions.findIndex(item => item.value === savedExchangeId)
  exchangeIndex.value = foundIndex >= 0 ? foundIndex : 1
  form.exchangeId = exchangeOptions[exchangeIndex.value].value
  form.runCount = config.runCount || form.runCount
  form.timeSleep = (config.timeSleep && Number(config.timeSleep) >= 0.15) ? config.timeSleep : form.timeSleep

  // 恢复每日任务完成状态
  dailyTaskDoneDate.value = config.dailyTaskDoneDate || ''
  const today = new Date().toISOString().slice(0, 10)
  if (dailyTaskDoneDate.value === today) {
    dailyTaskDone.value = true
  }

  // 调用 U005 验证 ses_id 是否仍然有效，同时获取用户姓名
  // 测试账号 admin 跳过验证
  if (form.loginName === 'admin' && form.sesId === 'test_ses_id') {
    userName.value = 'admin'
    remainIntegral.value = 999
    appendLog('欢迎, 测试管理员  当前积分: 999')
    appendLog('登录状态已恢复')
    persistConfig()
    startStatsPolling()
    return
  }

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
  startStatsPolling()
})

/** 页面卸载时停止统计轮询并上报下线 */
onUnload(() => {
  stopStatsPolling()
})

// ==================== 监听 ====================
/** 表单数据变化时自动持久化保存到本地存储 */
watch(form, () => { persistConfig() }, { deep: true })
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  box-sizing: border-box;
  background: #f8f9fa;
  font-family: "Google Sans", "Roboto", -apple-system, "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

/* ---------- 顶部横幅 ---------- */
.hero {
  margin-bottom: 20rpx;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 8rpx 2rpx rgba(60,64,67,.15), 0 1rpx 3rpx rgba(60,64,67,.30);
}

.hero-image {
  display: block;
  width: 100%;
}

/* ---------- 免责声明 ---------- */
.disclaimer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  margin-bottom: 24rpx;
  font-size: 24rpx;
  color: #5f6368;
}

/* ---------- 通用卡片（Material 3 surface + elevation） ---------- */
.card {
  background: #fff;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: 0 1rpx 3rpx rgba(60,64,67,.15), 0 4rpx 8rpx 2rpx rgba(60,64,67,.06);
  margin-bottom: 24rpx;
}

/* ---------- 登录状态卡片 ---------- */
.status-card {
  background: #fff;
}

.status-head {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.status-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 9999rpx;
  background: rgba(26, 115, 232, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-avatar-text {
  font-size: 36rpx;
  font-weight: 600;
  color: #1a73e8;
}

.status-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  overflow: hidden;
}

.status-user {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.status-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f1f1f;
}

.status-integral {
  font-size: 24rpx;
  color: #1e8e3e;
  font-weight: 500;
}

/* Material chip */
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  border-radius: 9999rpx;
  font-size: 22rpx;
  font-weight: 600;
  letter-spacing: 0.5rpx;
}

.chip-ok {
  background: rgba(30, 142, 62, 0.12);
  color: #1e8e3e;
}

.chip-bad {
  background: rgba(217, 48, 37, 0.12);
  color: #d93025;
}

/* ---------- 每日任务完成状态 ---------- */
.daily-status {
  display: flex;
  justify-content: center;
  margin-top: 16rpx;
}

.daily-status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  padding: 8rpx 24rpx;
  border-radius: 9999rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: #1e8e3e;
  background: #e6f4ea;
  border: 1rpx solid #a8dab5;
}

/* ---------- 卡片标题 ---------- */
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.title {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f1f1f;
  letter-spacing: 0.2rpx;
}

/* ---------- 实时统计 ---------- */
.stats-grid {
  display: flex;
  gap: 12rpx;
}

.stat-card {
  flex: 1;
  background: #f1f3f4;
  border-radius: 16rpx;
  padding: 16rpx 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}

.stat-label {
  font-size: 20rpx;
  color: #5f6368;
  font-weight: 500;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #1f1f1f;
}

/* ---------- 表单字段 ---------- */
.field {
  margin-bottom: 20rpx;
}

.inline {
  display: flex;
  gap: 16rpx;
}

.half {
  flex: 1;
}

.label {
  display: block;
  margin-bottom: 10rpx;
  color: #444746;
  font-size: 24rpx;
  font-weight: 500;
  letter-spacing: 0.2rpx;
}

/* Material 3 描边输入框 */
.input {
  width: 100%;
  height: 88rpx;
  border: 1.5rpx solid #dadce0;
  border-radius: 16rpx;
  padding: 0 22rpx;
  box-sizing: border-box;
  background: #fff;
  font-size: 28rpx;
  color: #1f1f1f;
}

.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.input-value {
  flex: 1;
}

.picker-arrow {
  color: #5f6368;
  font-size: 26rpx;
  padding-left: 12rpx;
}

/* ---------- 按钮组 ---------- */
.actions {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 8rpx;
}

.action-row {
  display: flex;
  gap: 14rpx;
}

.flex-1 {
  flex: 1;
}

.full {
  width: 100%;
}

/* Material 3 药丸按钮基类 */
.btn {
  border-radius: 9999rpx;
  font-size: 26rpx;
  font-weight: 600;
  height: 84rpx;
  line-height: 84rpx;
  padding: 0 28rpx;
  letter-spacing: 0.4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.btn-primary {
  background: #1a73e8;
  color: #fff;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 2rpx 6rpx 2rpx rgba(60,64,67,.15);
}

.btn-fill-error {
  background: #d93025;
  color: #fff;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 2rpx 6rpx 2rpx rgba(60,64,67,.15);
}

.btn-success {
  background: #1e8e3e;
  color: #fff;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 2rpx 6rpx 2rpx rgba(60,64,67,.15);
}

.btn-outline {
  background: transparent;
  color: #1a73e8;
  border: 1.5rpx solid #dadce0;
}

.btn-outline-danger {
  width: 100%;
  background: transparent;
  color: #d93025;
  border: 1.5rpx solid rgba(217, 48, 37, 0.4);
}

/* 禁用态 */
.btn[disabled] {
  color: #ffffff;
  background: rgba(0, 0, 0, 0.12) !important;
  border-color: transparent !important;
  box-shadow: none;
  opacity: 0.6;
}

.btn-outline[disabled],
.btn-outline-danger[disabled] {
  color: rgba(60, 64, 67, 0.38) !important;
  background: rgba(60, 64, 67, 0.06) !important;
  border-color: #dadce0 !important;
}

/* ---------- 运行日志 ---------- */
.log-box {
  height: 380rpx;
  border: 1rpx solid #e8eaed;
  border-radius: 16rpx;
  padding: 20rpx;
  box-sizing: border-box;
  background: #f8f9fa;
  font-family: "Roboto Mono", "Menlo", "Consolas", monospace;
}

.log-line {
  font-size: 22rpx;
  line-height: 1.7;
  margin-bottom: 6rpx;
  word-break: break-all;
  color: #444746;
}
</style>
