<template>
  <view class="page">
    <!-- 顶部横幅图片 -->
    <view class="hero">
      <image class="hero-image" src="../../resouse/home.jpg" mode="widthFix" />
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">仅供学习使用</view>

    <!-- 登录账号槽位：3 个圆形头像横排，与 Python 版一致 -->
    <view class="card accounts-card">
      <view class="card-head">
        <text class="title">登录</text>
      </view>

      <view class="accounts-row">
        <view
          v-for="(slot, idx) in accountSlots"
          :key="idx"
          class="account-slot"
          :class="{ active: idx === activeProfileIndex && slot.profile }"
          @click="onSlotClick(idx)"
        >
          <!-- 圆形头像区 -->
          <view class="avatar-wrap">
            <!-- 已登录：蓝色实心圆 + 首字 -->
            <view
              v-if="slot.profile && slot.loggedIn"
              class="avatar avatar-filled"
              @click.stop="switchProfile(idx)"
            >
              <text class="avatar-text">{{ avatarChar(slot.profile) }}</text>
              <view class="badge-dot"></view>
            </view>
            <!-- 未登录 / 空槽：灰色虚线圆 + 加号 -->
            <view v-else class="avatar avatar-empty" @click.stop="onSlotClick(idx)">
              <text class="avatar-plus">+</text>
            </view>
            <!-- 悬停/点击出现的红叉：仅已登录账号 -->
            <view
              v-if="slot.profile && slot.loggedIn"
              class="close-x"
              @click.stop="onSlotClose(idx)"
            >
              <text class="close-x-text">×</text>
            </view>
          </view>

          <!-- 右侧信息（4 行：名称 / 积分 / 每日任务 / 运行状态，避免积分被截断） -->
          <view class="slot-info">
            <template v-if="slot.profile && slot.loggedIn">
              <!-- 第 1 行：名称 -->
              <text class="slot-line slot-name">{{ displayName(slot.profile) }}</text>
              <!-- 第 2 行：积分（单独一行，保证一定可见） -->
              <text class="slot-line slot-integral">积分 {{ slot.integral }}</text>
              <!-- 第 3 行：每日任务状态 -->
              <text class="slot-line slot-task">{{ slot.dailyTaskDone ? '✅ 每日' : '☐ 每日' }}</text>
              <!-- 第 4 行：运行状态 -->
              <text
                class="slot-line slot-run"
                :style="{ color: slot.running ? '#67C23A' : '#E6A23C' }"
              >● {{ slot.running ? '运行中' : '未运行' }}</text>
            </template>
            <template v-else>
              <text class="slot-line slot-name-empty">{{ slot.profile ? slot.profile.name : '点击登录' }}</text>
              <text class="slot-line slot-integral slot-integral-empty">积分 —</text>
              <text class="slot-line slot-task">未登录</text>
              <text class="slot-line slot-run" style="color:#E6A23C;">● 未运行</text>
            </template>
          </view>
        </view>
      </view>
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
      </view>
    </view>

    <!-- 实时统计卡片（服务端 stats_enabled=false 时隐藏） -->
    <view class="card" v-if="statsVisible">
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
        <!-- 日志范围切换：全部账号 / 仅当前账号 -->
        <view class="log-filter" @click="showAllLogs = !showAllLogs">
          <text class="log-filter-text">{{ showAllLogs ? '全部账号' : '仅当前' }}</text>
        </view>
      </view>
      <scroll-view scroll-y class="log-box">
        <view
          class="log-line"
          :class="{ 'log-line-bold': typeof item === 'object' && item.bold }"
          v-for="(item, idx) in visibleLogs"
          :key="idx"
        >{{ typeof item === 'object' ? item.text : item }}</view>
        <view v-if="visibleLogs.length === 0" class="log-empty">暂无日志</view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import { runDailyTaskWorkflow, runExchangeOnce, isExchangeSuccess, isDailyTaskComplete } from '../../src/services/taskService'
import { loadAuth, loadConfig, saveProfiles, loadProfiles, saveActiveProfileIndex, loadActiveProfileIndex } from '../../src/utils/storage'
import { formatDateTime, getNextRunTime, parseDateTime } from '../../src/utils/time'
import { queryUserInfo, syncServerTime } from '../../src/services/authService'
import { isStatsEnabled, fetchStats, reportOnline, reportOffline, reportGrab } from '../../src/services/statsService'

// ==================== 多开 Profile 管理 ====================
/** 最多账号数：与 Python 版 3 个圆形头像槽位一致 */
const MAX_PROFILES = 3

/** Profile 列表 */
const profiles = ref([])
/** 当前选中的 Profile 索引 */
const activeProfileIndex = ref(0)

/** 当前选中的 Profile */
const currentProfile = computed(() => profiles.value[activeProfileIndex.value] || null)

/** 当前 Profile 的日志 */
const currentLogs = computed(() => currentProfile.value?.logs || [])

/** 是否显示全部账号的日志（默认全部，避免并发时只看得到当前账号） */
const showAllLogs = ref(true)

/**
 * 日志区实际展示的内容。
 *
 * 默认合并所有账号的日志——每条日志本身已带 `[时间] [账号名]` 前缀，
 * 合并后仍能一眼区分归属；两个账号同时跑任务时不会只剩当前账号的日志。
 */
const visibleLogs = computed(() => {
  if (!showAllLogs.value) {
    return currentLogs.value
  }
  const merged = []
  profiles.value.forEach((p) => {
    (p.logs || []).forEach((item) => merged.push(item))
  })
  // 按写入时间排序，保证并发时日志顺序正确
  merged.sort((a, b) => (a.ts || 0) - (b.ts || 0))
  return merged.length > 300 ? merged.slice(-300) : merged
})

/** 当前 Profile 是否已登录 */
const isLoggedIn = computed(() => Boolean(currentProfile.value?.auth?.loginName && currentProfile.value?.auth?.sesId))

/** 当前 Profile 是否正在运行任务 */
const running = computed(() => Boolean(currentProfile.value?.state?.running))
/** 当前 Profile 是否正在执行每日任务 */
const dailyTaskRunning = computed(() => Boolean(currentProfile.value?.state?.dailyTaskRunning))
/** 当前 Profile 每日任务是否已完成 */
const dailyTaskDone = computed(() => Boolean(currentProfile.value?.state?.dailyTaskDone))

/** 当前剩余积分 */
const remainIntegral = ref(0)

/**
 * 3 个账号槽位视图数据：固定渲染 3 个位置，
 * 每个槽位携带该账号的登录态、积分、运行态，互不影响。
 */
const accountSlots = computed(() => {
  const list = []
  for (let i = 0; i < MAX_PROFILES; i += 1) {
    const p = profiles.value[i] || null
    const loggedIn = Boolean(p && p.auth?.loginName && p.auth?.sesId && p.auth.isLoggedIn)
    list.push({
      profile: p,
      loggedIn,
      // 每个账号自己的积分，不再共用当前账号的 remainIntegral
      integral: Number(p?.auth?.remainIntegral || 0),
      // 每个账号自己的运行状态，与是否为当前选中账号无关
      running: Boolean(p?.state?.running),
      dailyTaskDone: Boolean(p?.state?.dailyTaskDone)
    })
  }
  return list
})

/** 取账号头像首字（优先真实姓名，其次账号名） */
function avatarChar(profile) {
  const name = profile?.auth?.displayName || profile?.name || '账'
  return String(name).slice(0, 1)
}

/** 取账号显示名（优先真实姓名，其次账号名） */
function displayName(profile) {
  return profile?.auth?.displayName || profile?.auth?.loginName || profile?.name || '未登录'
}

/** 取本地时区的今天日期（YYYY-MM-DD）
 *
 * 不能用 toISOString()：那是 UTC 日期，东八区早上 8 点前会算成前一天，
 * 导致每日任务的"今天已完成"判断跨日错乱。
 */
function localToday() {
  const d = new Date()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

/** 配置表单（绑定当前 Profile） */
const form = reactive({
  loginName: '',
  userId: '',
  sesId: '',
  exchangeId: '10',
  runTime: getNextRunTime(),
  runCount: '10',
  timeSleep: '0.2'
})

/** 优惠券面额选项 */
const exchangeOptions = [
  { label: '2元优惠券', value: '9' },
  { label: '4元优惠券', value: '10' },
  { label: '6元优惠券', value: '11' }
]
/** 当前选中的优惠券面额索引 */
const exchangeIndex = ref(1)

// ==================== 实时统计（全局共享） ====================
const statsEnabled = isStatsEnabled()
const statsOnline = ref(0)
const statsType9 = ref(0)
const statsType10 = ref(0)
const statsType11 = ref(0)
/**
 * 统计模块是否显示。
 *
 * 初始为 false：等第一次轮询拿到服务端数据后再决定是否显示，
 * 避免启动瞬间闪出一个全 0 的面板。
 * 与 statsEnabled（本地是否配置了服务端地址）是两个独立概念。
 */
const statsVisible = ref(false)
let statsTimer = null

// ==================== 账号槽位交互 ====================

/**
 * 点击槽位：
 * - 已登录 → 切换到该账号
 * - 未登录 → 跳转登录页，登录后写回该槽位
 * - 空槽位 → 新建账号并跳转登录页
 */
function onSlotClick(idx) {
  const p = profiles.value[idx]
  const loggedIn = Boolean(p && p.auth?.loginName && p.auth?.sesId && p.auth.isLoggedIn)

  if (loggedIn) {
    switchProfile(idx)
    return
  }

  // 未登录 / 空槽位：进入登录页登录该槽位
  goLoginForSlot(idx)
}

/** 跳转登录页并为指定槽位登录 */
function goLoginForSlot(idx) {
  // 确保槽位存在，不存在则先创建
  while (profiles.value.length <= idx && profiles.value.length < MAX_PROFILES) {
    createEmptyProfile()
  }
  if (!profiles.value[idx]) {
    uni.showToast({ title: `最多 ${MAX_PROFILES} 个账号`, icon: 'none' })
    return
  }
  // 记录目标槽位，登录页登录成功后写回这里
  saveActiveProfileIndex(idx)
  activeProfileIndex.value = idx
  uni.navigateTo({ url: `/pages/login/login?slot=${idx}` })
}

/** 创建一个空 Profile（不切换选中） */
function createEmptyProfile() {
  profiles.value.push({
    id: 'profile_' + Date.now() + '_' + profiles.value.length,
    name: `账号${profiles.value.length + 1}`,
    auth: {
      loginName: '',
      userId: '',
      sesId: '',
      isLoggedIn: false,
      displayName: '',
      remainIntegral: 0
    },
    config: {
      exchangeId: '10',
      runTime: getNextRunTime(),
      runCount: '10',
      timeSleep: '0.2'
    },
    state: {
      running: false,
      stopRequested: false,
      dailyTaskRunning: false,
      dailyTaskDone: false,
      dailyTaskDoneDate: '',
      timerId: null
    },
    logs: []
  })
  return profiles.value[profiles.value.length - 1]
}

/**
 * 点击红色 ×：退出该账号登录。
 * 该账号有任务在跑时先阻止，避免任务中途掉凭证。
 */
function onSlotClose(idx) {
  const p = profiles.value[idx]
  if (!p) return

  if (p.state?.running || p.state?.dailyTaskRunning) {
    uni.showToast({ title: '请先停止该账号的任务', icon: 'none' })
    return
  }

  uni.showModal({
    title: '退出登录',
    content: `确定退出 ${displayName(p)} 吗？`,
    confirmText: '退出',
    confirmColor: '#F56C6C',
    success: (res) => {
      if (res.confirm) doLogoutSlot(idx)
    }
  })
}

/** 执行某个槽位的退出登录 */
function doLogoutSlot(idx) {
  const p = profiles.value[idx]
  if (!p) return

  p.auth.loginName = ''
  p.auth.userId = ''
  p.auth.sesId = ''
  p.auth.isLoggedIn = false
  p.auth.displayName = ''
  p.auth.remainIntegral = 0
  p.state.running = false
  p.state.dailyTaskRunning = false
  p.state.dailyTaskDone = false
  p.state.dailyTaskDoneDate = ''
  if (p.state.timerId) {
    clearTimeout(p.state.timerId)
    p.state.timerId = null
  }
  p.logs = []

  if (idx === activeProfileIndex.value) {
    remainIntegral.value = 0
  }

  saveProfiles(profiles.value)
  uni.showToast({ title: '已退出登录', icon: 'none' })
}

// ==================== Profile 操作 ====================

/** 创建新 Profile 并切换过去 */
function addProfile() {
  if (profiles.value.length >= MAX_PROFILES) {
    uni.showToast({ title: `最多 ${MAX_PROFILES} 个账号`, icon: 'none' })
    return
  }
  createEmptyProfile()
  activeProfileIndex.value = profiles.value.length - 1
  saveProfiles(profiles.value)
  saveActiveProfileIndex(activeProfileIndex.value)
  syncFormFromProfile()
  appendLog('已创建新账号，请登录')
}

/** 切换 Profile */
function switchProfile(index) {
  if (index === activeProfileIndex.value) return
  const p = profiles.value[index]
  if (!p) return
  activeProfileIndex.value = index
  saveActiveProfileIndex(index)
  syncFormFromProfile()
}

/** 从当前 Profile 同步数据到表单 */
function syncFormFromProfile() {
  const p = currentProfile.value
  if (!p) {
    // 没有 Profile，清空表单
    form.loginName = ''
    form.userId = ''
    form.sesId = ''
    form.exchangeId = '10'
    form.runTime = getNextRunTime()
    form.runCount = '10'
    form.timeSleep = '0.2'
    remainIntegral.value = 0
    return
  }

  form.loginName = p.auth.loginName || ''
  form.userId = p.auth.userId || ''
  form.sesId = p.auth.sesId || ''
  form.exchangeId = p.config.exchangeId || '10'
  form.runTime = p.config.runTime || getNextRunTime()
  form.runCount = p.config.runCount || '10'
  form.timeSleep = p.config.timeSleep || '0.2'

  // 同步 exchangeIndex
  const idx = exchangeOptions.findIndex(item => item.value === form.exchangeId)
  exchangeIndex.value = idx >= 0 ? idx : 1

  // 同步该账号自己的积分
  remainIntegral.value = Number(p.auth.remainIntegral || 0)
}

/** 将表单数据保存回当前 Profile */
function syncProfileFromForm() {
  const p = currentProfile.value
  if (!p) return

  p.auth = p.auth || {}
  p.config = p.config || {}

  p.auth.loginName = form.loginName
  p.auth.userId = form.userId
  p.auth.sesId = form.sesId
  p.auth.isLoggedIn = Boolean(form.loginName && form.sesId)

  p.config.exchangeId = form.exchangeId
  p.config.runTime = form.runTime
  p.config.runCount = form.runCount
  p.config.timeSleep = form.timeSleep

  saveProfiles(profiles.value)
}

// ==================== 日志 ====================
/**
 * 追加日志到指定 Profile（默认当前 Profile）。
 *
 * 关键点：任务日志必须写回"发起任务的账号"，而不是"当前选中的账号"，
 * 否则两个账号同时跑任务时日志会全部串到当前账号上。
 *
 * @param {string} message 日志内容
 * @param {object} [profile] 目标 Profile，缺省为当前选中账号
 */
function appendLog(message, profile) {
  const p = profile || currentProfile.value
  if (!p) return
  const now = new Date()
  const ts = formatDateTime(now)
  const name = p.auth?.displayName || p.auth?.loginName || p.name || '未登录'
  const text = String(message)
  // 抢到票的消息加粗高亮
  const bold = text.includes('抢到') || text.includes('兑换成功')
  p.logs = p.logs || []
  p.logs.push({
    text: `[${ts}] [${name}] ${text}`,
    bold,
    // 合并多账号日志时按此字段排序
    ts: now.getTime()
  })
  // 限制日志数量，防止内存溢出
  if (p.logs.length > 200) {
    p.logs = p.logs.slice(-100)
  }
}

// ==================== 任务操作 ====================

/** 停止当前账号的兑换任务（不影响其他账号） */
function stopProgram() {
  const p = currentProfile.value
  if (!p) return

  p.state.stopRequested = true
  p.state.running = false
  if (p.state.timerId) {
    clearTimeout(p.state.timerId)
    p.state.timerId = null
  }
  appendLog('程序已停止', p)
  saveProfiles(profiles.value)
}

/** 启动当前账号的兑换任务（各账号独立运行，互不影响） */
async function startProgram() {
  const p = currentProfile.value
  if (!p) return

  if (p.state.running) {
    uni.showToast({ title: '该账号任务已在运行中', icon: 'none' })
    return
  }

  // 任务开始前把日志写回本账号，后续即使切换账号也不会串
  const ownerProfile = p

  try {
    syncProfileFromForm()
    const { runCount, timeSleep, runDate } = validateInputs()

    p.state.stopRequested = false
    p.state.running = true
    appendLog('正在同步服务器时间...', ownerProfile)

    let offset = 0
    try {
      const serverTime = await syncServerTime(ownerProfile.auth.loginName, ownerProfile.auth.sesId)
      offset = serverTime - Date.now()
      appendLog(`服务器时间同步完成，本地偏移: ${offset > 0 ? '+' : ''}${offset}ms`, ownerProfile)
    } catch (error) {
      appendLog(`服务器时间同步失败，使用本地时间: ${error.message}`, ownerProfile)
    }

    appendLog(`程序已启动，将在 ${form.runTime} 执行兑换任务，共执行 ${runCount} 次`, ownerProfile)

    // 基于服务器时间计算等待毫秒数
    const waitMs = Math.max(runDate.getTime() - (Date.now() + offset), 0)
    p.state.timerId = setTimeout(async () => {
      // 本轮任务的抢到标记：同一轮只上报一次，与 Python 版 _grab_reported 语义一致
      let grabReported = false
      for (let i = 0; i < runCount; i += 1) {
        if (ownerProfile.state.stopRequested) break
        appendLog(`准备执行第 ${i + 1} 次兑换请求`, ownerProfile)
        runExchangeOnce({
          loginName: ownerProfile.auth.loginName,
          userId: ownerProfile.auth.userId || ownerProfile.auth.loginName,
          sesId: ownerProfile.auth.sesId,
          exchangeId: ownerProfile.config.exchangeId,
          log: (msg) => appendLog(msg, ownerProfile)
        }).then((parsed) => {
          if (isExchangeSuccess(parsed) && !grabReported) {
            grabReported = true
            reportGrab(
              ownerProfile.config.exchangeId,
              ownerProfile.auth.userId || ownerProfile.auth.loginName
            )
            appendLog('🎉 抢到票了！正在上报统计...', ownerProfile)
            // 成功后后台刷新积分，让槽位上的积分同步下降
            refreshIntegral(ownerProfile)
          }
        }).catch((error) => {
          appendLog(`兑换请求失败: ${error.message}`, ownerProfile)
        })

        if (i < runCount - 1 && !ownerProfile.state.stopRequested) {
          await new Promise((resolve) => {
            ownerProfile.state.timerId = setTimeout(resolve, Math.max(timeSleep * 1000, 20))
          })
        }
      }

      ownerProfile.state.running = false
      if (!ownerProfile.state.stopRequested) {
        appendLog('程序执行完成', ownerProfile)
      }
      ownerProfile.state.timerId = null
      saveProfiles(profiles.value)
      // 任务结束后立即拉一次统计，避免刚上报的数字要等下一个 60 秒才显示
      if (grabReported) fetchAndShowStats()
    }, waitMs)
  } catch (error) {
    p.state.running = false
    uni.showToast({ title: error.message, icon: 'none' })
  }
}

/** 执行当前账号的每日任务工作流 */
async function runDailyTask() {
  const p = currentProfile.value
  if (!p) return

  if (!p.auth.loginName || !p.auth.sesId) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }

  if (p.state.dailyTaskRunning) {
    uni.showToast({ title: '该账号每日任务正在执行中', icon: 'none' })
    return
  }

  const ownerProfile = p
  syncProfileFromForm()
  p.state.dailyTaskRunning = true
  p.state.dailyTaskDone = false
  appendLog('开始执行每日任务工作流', ownerProfile)
  try {
    const steps = await runDailyTaskWorkflow({
      loginName: ownerProfile.auth.loginName,
      sesId: ownerProfile.auth.sesId,
      log: (msg) => appendLog(msg, ownerProfile)
    })
    // 只有每一步都成功才算完成，避免部分失败也标记已做
    const ok = isDailyTaskComplete(steps)
    ownerProfile.state.dailyTaskDone = ok
    ownerProfile.state.dailyTaskDoneDate = ok ? localToday() : ''
    saveProfiles(profiles.value)
    // 每日任务后刷新积分
    await refreshIntegral(ownerProfile)
    appendLog(ok ? '每日任务执行完成' : '每日任务未全部成功，请查看上方日志', ownerProfile)
  } catch (error) {
    appendLog(`每日任务执行失败: ${error.message}`, ownerProfile)
  } finally {
    ownerProfile.state.dailyTaskRunning = false
    saveProfiles(profiles.value)
  }
}

/** 查询并刷新某账号的积分与真实姓名，写回该账号 */
async function refreshIntegral(profile) {
  const p = profile || currentProfile.value
  if (!p || !p.auth.loginName || !p.auth.sesId) return
  try {
    const userInfo = await queryUserInfo(p.auth.loginName, p.auth.sesId)
    if (userInfo && userInfo.result === '0') {
      const name = userInfo.name || userInfo.sensitive_name || ''
      if (name) p.auth.displayName = name
      p.auth.remainIntegral = parseInt(userInfo.remain_integral) || 0
      if (p === currentProfile.value) {
        remainIntegral.value = p.auth.remainIntegral
      }
      saveProfiles(profiles.value)
    }
  } catch {
    // 静默失败，不影响主流程
  }
}

/** 退出登录（当前账号） */
function logout() {
  const idx = activeProfileIndex.value
  const p = currentProfile.value
  if (!p) return
  if (p.state.running || p.state.dailyTaskRunning) {
    uni.showToast({ title: '请先停止任务后再退出登录', icon: 'none' })
    return
  }
  doLogoutSlot(idx)
  // 如果所有 Profile 都未登录，跳转到登录页
  const anyLoggedIn = profiles.value.some(profile => profile.auth.isLoggedIn)
  if (!anyLoggedIn) {
    uni.redirectTo({ url: '/pages/login/login' })
  }
}

/** 跳转到绿色出行二维码页面 */
function goQrCode() {
  const p = currentProfile.value
  if (!p || !p.auth.loginName || !p.auth.sesId) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  uni.navigateTo({ url: '/pages/qrcode/qrcode' })
}

// ==================== 工具函数 ====================

/** 校验输入参数 */
function validateInputs() {
  const p = currentProfile.value
  if (!p) throw new Error('请先创建账号')

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

/** 优惠券面额切换 */
function onExchangeChange(e) {
  exchangeIndex.value = e.detail.value
  form.exchangeId = exchangeOptions[exchangeIndex.value].value
  syncProfileFromForm()
}

// ==================== 实时统计 ====================
/**
 * 拉取一次统计数据并刷新界面，同时按服务端开关控制模块显隐。
 *
 * 拿不到数据（网络故障、域名不通、服务端返回异常）时一律隐藏：
 * 显示一个全 0 的统计面板比不显示更误导，用户会以为真的没人抢到。
 */
async function fetchAndShowStats() {
  let data = null
  try {
    data = await fetchStats()
  } catch {
    data = null
  }
  if (!data) {
    statsVisible.value = false
    return
  }
  // 服务端开关：false 时隐藏整个实时统计模块
  statsVisible.value = data.stats_enabled !== false
  if (!statsVisible.value) return

  statsOnline.value = data.online
  statsType9.value = data.by_type['9'] || 0
  statsType10.value = data.by_type['10'] || 0
  statsType11.value = data.by_type['11'] || 0
}

/**
 * 收集所有已登录账号的统计标识。
 *
 * 服务端按 client_id 去重，同一台手机/电脑跑多个账号时若共用一个标识，
 * 在线人数永远只有 1。这里给每个账号返回独立标识。
 */
function getLoggedInAccountKeys() {
  const keys = []
  for (const profile of profiles.value) {
    const auth = profile?.auth || {}
    if (!(auth.isLoggedIn && auth.loginName && auth.sesId)) continue
    const key = String(auth.userId || auth.loginName || '').trim()
    if (key && !keys.includes(key)) keys.push(key)
  }
  return keys
}

/**
 * 心跳 + 拉取统计。
 *
 * 服务端在线数是滑动窗口（2 分钟内有心跳才算在线），所以每次轮询
 * 必须给所有已登录账号发 open 刷新 last_seen，否则 2 分钟后自己
 * 就从在线列表里掉出去。多账号各自一条在线记录。
 */
async function pollStats() {
  const keys = getLoggedInAccountKeys()
  if (keys.length > 0) {
    await Promise.all(keys.map(k => reportOnline('open', k)))
  } else {
    await reportOnline('open')
  }
  await fetchAndShowStats()
}

/** 启动统计轮询（每 60 秒刷新一次，同时兼作心跳） */
function startStatsPolling() {
  if (!statsEnabled) return
  pollStats()
  statsTimer = setInterval(pollStats, 60000)
}

/** 停止统计轮询 */
function stopStatsPolling() {
  if (statsTimer) {
    clearInterval(statsTimer)
    statsTimer = null
  }
  const keys = getLoggedInAccountKeys()
  if (keys.length > 0) {
    keys.forEach(k => reportOffline(k))
  } else {
    reportOffline()
  }
}

// ==================== 生命周期 ====================

onLoad(async (options) => {
  // 迁移旧数据：如果存在旧的 auth/config，创建第一个 Profile
  migrateLegacyData()

  // 加载 Profile 列表
  const savedProfiles = loadProfiles()
  const savedIndex = loadActiveProfileIndex()

  if (savedProfiles.length > 0) {
    profiles.value = savedProfiles
    // 登录页回跳时指定了目标槽位，优先使用
    const slotFromQuery = options && options.slot !== undefined ? Number(options.slot) : null
    const targetIndex = slotFromQuery !== null && Number.isFinite(slotFromQuery)
      ? slotFromQuery
      : savedIndex
    activeProfileIndex.value = Math.min(Math.max(targetIndex, 0), Math.max(savedProfiles.length - 1, 0))
  } else {
    // 没有 Profile，创建一个空的
    addProfile()
    uni.showToast({ title: '请登录账号', icon: 'none' })
    return
  }

  // 清除上次退出时残留的运行标记（定时器不会跨启动恢复）
  profiles.value.forEach((profile) => {
    profile.state = profile.state || {}
    profile.state.running = false
    profile.state.dailyTaskRunning = false
    profile.state.stopRequested = false
    profile.state.timerId = null
  })

  // 同步当前 Profile 到表单
  syncFormFromProfile()

  // 恢复每个账号的每日任务完成状态（只认今天的记录）
  const today = localToday()
  profiles.value.forEach((profile) => {
    profile.state = profile.state || {}
    profile.state.dailyTaskDone = Boolean(profile.state.dailyTaskDoneDate === today)
  })

  // 刷新所有已登录账号的积分/姓名，让每个槽位都能显示自己的积分
  await Promise.all(
    profiles.value
      .filter(profile => profile.auth?.isLoggedIn && profile.auth?.loginName && profile.auth?.sesId)
      .map(profile => refreshIntegral(profile))
  )

  saveProfiles(profiles.value)
  syncFormFromProfile()

  startStatsPolling()

  // 登录进来自动检查并补齐每日任务（后台执行，不阻塞界面）
  autoRunDailyTasks()
})

/**
 * 登录后自动检查每日任务。
 *
 * U042 接口没有「只查询不执行」的模式，所以只能真的执行一遍来确认完成。
 * 因此这里只对「今天还没做过」的已登录账号执行，避免重复消耗。
 * 多个账号串行执行，避免同一时间打太多请求。
 */
async function autoRunDailyTasks() {
  const today = localToday()
  const targets = profiles.value.filter(profile =>
    profile.auth?.isLoggedIn &&
    profile.auth?.loginName &&
    profile.auth?.sesId &&
    profile.state?.dailyTaskDoneDate !== today &&
    !profile.state?.dailyTaskRunning
  )
  if (targets.length === 0) return

  for (const profile of targets) {
    // 执行期间可能被用户切走，这里直接操作 ownerProfile，不依赖当前选中项
    const ownerProfile = profile
    try {
      ownerProfile.state.dailyTaskRunning = true
      appendLog('自动执行每日任务', ownerProfile)
      const steps = await runDailyTaskWorkflow({
        loginName: ownerProfile.auth.loginName,
        sesId: ownerProfile.auth.sesId,
        log: (msg) => appendLog(msg, ownerProfile)
      })
      const ok = isDailyTaskComplete(steps)
      ownerProfile.state.dailyTaskDone = ok
      ownerProfile.state.dailyTaskDoneDate = ok ? today : ''
      appendLog(ok ? '每日任务已完成' : '每日任务未全部成功', ownerProfile)
      await refreshIntegral(ownerProfile)
    } catch (error) {
      appendLog(`自动执行每日任务失败: ${error.message}`, ownerProfile)
    } finally {
      ownerProfile.state.dailyTaskRunning = false
      saveProfiles(profiles.value)
    }
  }
}

/** 迁移旧版本数据到 Profile 结构 */
function migrateLegacyData() {
  const oldProfiles = loadProfiles()
  if (oldProfiles.length > 0) return // 已有 Profile 数据，无需迁移

  const auth = loadAuth()
  const config = loadConfig()

  if (!auth || !auth.loginName) return // 没有旧数据

  // 创建第一个 Profile，迁移旧数据
  const migratedProfile = {
    id: 'profile_1',
    name: '账号1',
    auth: {
      loginName: auth.loginName || '',
      userId: auth.userId || auth.loginName || '',
      sesId: auth.sesId || '',
      isLoggedIn: auth.isLoggedIn || false,
      displayName: auth.displayName || '',
      remainIntegral: Number(auth.remainIntegral || 0)
    },
    config: {
      exchangeId: config.exchangeId || '10',
      runTime: config.runTime || getNextRunTime(),
      runCount: config.runCount || '10',
      timeSleep: config.timeSleep || '0.2'
    },
    state: {
      running: false,
      stopRequested: false,
      dailyTaskRunning: false,
      dailyTaskDone: config.dailyTaskDoneDate === localToday(),
      dailyTaskDoneDate: config.dailyTaskDoneDate || '',
      timerId: null
    },
    logs: []
  }

  profiles.value = [migratedProfile]
  activeProfileIndex.value = 0
  saveProfiles(profiles.value)
  saveActiveProfileIndex(0)
}

onUnload(() => {
  stopStatsPolling()
})

// ==================== 监听 ====================
/** 表单数据变化时自动保存到当前 Profile */
watch(form, () => { syncProfileFromForm() }, { deep: true })
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
  box-shadow: 0 1px 2px rgba(60,64,67,.3), 0 2px 6px 2px rgba(60,64,67,.15);
}

.hero-image {
  width: 100%;
  display: block;
}

.disclaimer {
  text-align: center;
  font-size: 22rpx;
  color: #9aa0a6;
  margin-bottom: 24rpx;
  letter-spacing: 2rpx;
}

/* ---------- 账号槽位（3 个圆形头像横排） ---------- */
.accounts-card {
  padding: 28rpx 24rpx;
}

.accounts-row {
  display: flex;
  flex-direction: row;
  gap: 12rpx;
}

.account-slot {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10rpx;
  padding: 10rpx 8rpx;
  border-radius: 20rpx;
  box-sizing: border-box;
}

.account-slot.active {
  background: rgba(26, 115, 232, 0.06);
}

/* 头像容器：承载圆形头像与右上角红叉 */
.avatar-wrap {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  flex-shrink: 0;
}

/* 已登录头像：蓝色实心圆 + 首字 */
.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-sizing: border-box;
}

.avatar-filled {
  background: #1a73e8;
  border: 3rpx solid #1a73e8;
}

.avatar-text {
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1;
}

/* 未登录 / 空槽：灰色虚线圆 + 加号 */
.avatar-empty {
  background: #f1f3f4;
  border: 3rpx dashed #bdc1c6;
}

.avatar-plus {
  color: #9aa0a6;
  font-size: 44rpx;
  font-weight: 300;
  line-height: 1;
}

/* 绿色在线小圆点 */
.badge-dot {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 22rpx;
  height: 22rpx;
  border-radius: 50%;
  background: #34a853;
  border: 3rpx solid #ffffff;
  box-sizing: border-box;
}

/* 右上角红色 × */
.close-x {
  position: absolute;
  top: -4rpx;
  right: -4rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: #F56C6C;
  border: 3rpx solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.close-x-text {
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
}

/* 右侧四行信息：名称 / 积分 / 每日任务 / 运行状态 */
.slot-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.slot-line {
  font-size: 20rpx;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slot-name {
  font-size: 22rpx;
  font-weight: 600;
  color: #1f1f1f;
}

.slot-integral {
  font-size: 20rpx;
  color: #67C23A;
  font-weight: 600;
}

/* 未登录槽位的积分占位 */
.slot-integral-empty {
  color: #9aa0a6 !important;
  font-weight: 500;
}

.slot-name-empty {
  font-size: 22rpx;
  font-weight: 500;
  color: #5f6368;
}

.slot-task {
  color: #5f6368;
}

.slot-run {
  font-size: 20rpx;
  font-weight: 600;
}

/* ---------- 卡片通用 ---------- */
.card {
  background: #ffffff;
  border-radius: 28rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 1px 2px rgba(60,64,67,.3), 0 2px 6px 2px rgba(60,64,67,.15);
}

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

/* ---------- 登录状态卡片 ---------- */
.status-card {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.status-head {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.status-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: rgba(26, 115, 232, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-avatar-text {
  font-size: 40rpx;
  font-weight: 600;
  color: #1a73e8;
}

.status-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.status-user {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.status-name {
  font-size: 32rpx;
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

/* ---------- 表单字段 ---------- */
.field {
  margin-bottom: 24rpx;
}

.field.inline {
  display: flex;
  gap: 20rpx;
}

.half {
  flex: 1;
}

.label {
  font-size: 24rpx;
  color: #5f6368;
  margin-bottom: 12rpx;
  display: block;
}

.input {
  width: 100%;
  height: 92rpx;
  padding: 0 28rpx;
  background: #ffffff;
  border: 1.5rpx solid #dadce0;
  border-radius: 16rpx;
  font-size: 28rpx;
  color: #1f1f1f;
  box-sizing: border-box;
}

.input:focus {
  border-color: #1a73e8;
  border-width: 2rpx;
}

.input-value {
  color: #1f1f1f;
}

.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-arrow {
  color: #5f6368;
  font-size: 24rpx;
}

/* ---------- 按钮 ---------- */
.actions {
  margin-top: 32rpx;
}

.action-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.action-row:last-child {
  margin-bottom: 0;
}

.btn {
  height: 92rpx;
  border-radius: 9999rpx;
  font-size: 28rpx;
  font-weight: 600;
  letter-spacing: 0.4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: none;
}

.btn-primary {
  background: #1a73e8;
  color: #fff;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 2rpx 6rpx 2rpx rgba(60,64,67,.15);
}

.btn-fill-error {
  background: #d93025;
  color: #fff;
}

.btn-outline {
  background: transparent;
  color: #1a73e8;
  border: 1.5rpx solid #dadce0;
}

.btn-outline-danger {
  background: transparent;
  color: #d93025;
  border: 1.5rpx solid #d93025;
}

.btn-success {
  background: #1e8e3e;
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
}

.flex-1 {
  flex: 1;
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

/* ---------- 日志 ---------- */
.log-box {
  height: 400rpx;
  background: #f8f9fa;
  border-radius: 16rpx;
  padding: 20rpx;
  box-sizing: border-box;
}

.log-line {
  font-size: 22rpx;
  color: #444746;
  line-height: 1.6;
  margin-bottom: 8rpx;
  word-break: break-all;
}

/* 抢到票 / 兑换成功的日志加粗高亮 */
.log-line-bold {
  font-weight: 700;
  color: #67C23A;
}

/* 日志范围切换按钮 */
.log-filter {
  padding: 6rpx 20rpx;
  border-radius: 9999rpx;
  background: #f1f3f4;
}

.log-filter-text {
  font-size: 22rpx;
  color: #1a73e8;
  font-weight: 600;
}

/* 日志空状态 */
.log-empty {
  font-size: 22rpx;
  color: #9aa0a6;
  text-align: center;
  padding: 40rpx 0;
}
</style>
