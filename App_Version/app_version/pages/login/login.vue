<template>
  <view class="page">
    <!-- 顶部横幅图片 -->
    <view class="hero">
      <image class="hero-image" src="../../resouse/login.jpg" mode="widthFix" />
    </view>

    <!-- 免责声明 -->
    <view class="disclaimer">仅供学习使用</view>

    <view class="card">
      <!-- 品牌标识 -->
      <view class="brand">
        <view class="brand-mark">
          <text class="brand-mark-text">A</text>
        </view>
        <text class="title">e家登录</text>
        <text class="subtitle">请使用手机号完成登录</text>
      </view>

      <!-- 登录方式切换：Material 3 分段按钮 -->
      <view class="segmented">
        <view
          class="seg-item"
          :class="{ active: loginMode === 'password' }"
          @click="loginMode = 'password'"
        >密码登录</view>
        <view
          class="seg-item"
          :class="{ active: loginMode === 'sms' }"
          @click="switchToSms"
        >短信验证码登录</view>
      </view>

      <!-- 手机号输入（两种登录方式共用） -->
      <view class="field">
        <text class="label">手机号</text>
        <input v-model="phone" class="input" placeholder="请输入手机号" placeholder-style="color:#5f6368;" />
      </view>

      <!-- 密码输入（仅密码登录模式显示） -->
      <template v-if="loginMode === 'password'">
        <view class="field">
          <text class="label">密码</text>
          <input v-model="password" class="input" password placeholder="请输入密码" placeholder-style="color:#5f6368;" />
        </view>
      </template>

      <!-- 图形验证码区域：显示验证码图片 + 刷新按钮 -->
      <view class="field">
        <text class="label">图形验证码</text>
        <view class="captcha-row">
          <view class="captcha-frame">
            <image v-if="captchaImage" :src="captchaImage" :key="captchaImage" mode="scaleToFill"
              class="captcha-img"
              @error="onCaptchaImageError" @load="onImageLoadSuccess" />
            <text v-else class="captcha-placeholder">正在渲染...</text>
          </view>
          <button class="btn btn-outline btn-refresh" @click="refreshCaptcha" :disabled="loadingCaptcha">
            {{ loadingCaptcha ? '获取中...' : '刷新' }}
          </button>
        </view>
      </view>

      <!-- 用户输入图形验证码 -->
      <view class="field">
        <text class="label">输入验证码</text>
        <input v-model="captchaCode" class="input" placeholder="请输入图形验证码" placeholder-style="color:#5f6368;" />
      </view>

      <!-- 短信验证码登录额外字段：短信验证码输入 + 获取按钮 -->
      <template v-if="loginMode === 'sms'">
        <view class="field">
          <text class="label">短信验证码</text>
          <view class="sms-row">
            <input v-model="smsCode" class="input sms-input" placeholder="请输入短信验证码" placeholder-style="color:#5f6368;" />
            <button
              class="btn btn-outline btn-sms"
              :disabled="sendingSms || smsCountdown > 0"
              @click="handleSendSms"
            >
              {{ smsCountdown > 0 ? `${smsCountdown}s` : (sendingSms ? '发送中...' : '获取验证码') }}
            </button>
          </view>
        </view>
      </template>

      <!-- 登录提交按钮 -->
      <button class="btn btn-primary" @click="submitLogin" :disabled="submitting">
        {{ submitting ? '登录中...' : '登录' }}
      </button>

      <!-- 用户协议与隐私政策 -->
      <view class="agreement-row">
        <checkbox-group @change="onAgreementChange">
          <checkbox :checked="agreed" value="1" color="#1a73e8" />
        </checkbox-group>
        <view class="agreement-text">
          <text>我已阅读并同意</text>
          <text class="link" @click="openAgreement('user')">《用户服务协议》</text>
          <text>和</text>
          <text class="link" @click="openAgreement('privacy')">《隐私政策》</text>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { decodeCaptchaImage, getCaptchaU067, loginU004WithCode, sendSms, loginU065 } from '../../src/services/authService'
import { loadAuth, saveAuth, loadProfiles, saveProfiles, loadActiveProfileIndex, saveActiveProfileIndex } from '../../src/utils/storage'

// ==================== 响应式状态定义 ====================
/** 当前登录模式：'password' 密码登录 / 'sms' 短信验证码登录 */
const loginMode = ref('password')
/** 手机号输入 */
const phone = ref('')
/** 密码输入 */
const password = ref('')
/** 用户输入的图形验证码 */
const captchaCode = ref('')
/** 图形验证码图片本地路径（用于 <image> 显示） */
const captchaImage = ref('')
/** 从接口获取的图形验证码原始数据（用于提交登录） */
const captchaData = ref(null)
/** 是否正在加载验证码 */
const loadingCaptcha = ref(false)
/** 是否正在提交登录请求 */
const submitting = ref(false)

/** 短信验证码输入 */
const smsCode = ref('')
/** 是否正在发送短信验证码 */
const sendingSms = ref(false)
/** 短信验证码发送后倒计时秒数 */
const smsCountdown = ref(0)
/** 倒计时定时器句柄 */
let countdownTimer = null
/** 是否已同意用户协议与隐私政策 */
const agreed = ref(false)

// ==================== 账号槽位 ====================
/** 最多账号数：与 Python 版 3 个圆形头像槽位一致 */
const MAX_PROFILES = 3
/** 本次登录要写入的槽位索引（由主页面槽位跳转传入，-1 表示未指定） */
let targetSlotIndex = -1

// ==================== Profile 管理 ====================
/**
 * 将登录信息保存到目标 Profile。
 *
 * @param {string} loginName 账号
 * @param {string} userId 用户 ID
 * @param {string} sesId 会话 ID
 * @param {object} [extra] 额外信息：displayName 真实姓名 / remainIntegral 积分
 */
function saveLoginToProfile(loginName, userId, sesId, extra = {}) {
  const profiles = loadProfiles()
  // 登录页可能由某个账号槽位跳转而来，优先写回该槽位
  let targetIndex = typeof targetSlotIndex === 'number' && targetSlotIndex >= 0
    ? targetSlotIndex
    : loadActiveProfileIndex()

  // 槽位不存在则按需补齐
  while (profiles.length <= targetIndex && profiles.length < MAX_PROFILES) {
    profiles.push({
      id: 'profile_' + Date.now() + '_' + profiles.length,
      name: `账号${profiles.length + 1}`,
      auth: { loginName: '', userId: '', sesId: '', isLoggedIn: false, displayName: '', remainIntegral: 0 },
      config: { exchangeId: '10', runTime: '', runCount: '10', timeSleep: '0.2' },
      state: { running: false, stopRequested: false, dailyTaskRunning: false, dailyTaskDone: false, dailyTaskDoneDate: '', timerId: null },
      logs: []
    })
  }

  // 索引越界时回退到 0
  if (targetIndex >= profiles.length) {
    targetIndex = profiles.length - 1
  }
  if (targetIndex < 0) {
    targetIndex = 0
  }

  const profile = profiles[targetIndex]
  profile.auth = profile.auth || {}
  profile.auth.loginName = loginName
  profile.auth.userId = userId || loginName
  profile.auth.sesId = sesId
  profile.auth.isLoggedIn = true
  // 真实姓名与账号标识分开保存，日志/头像都用真实姓名
  if (extra.displayName) {
    profile.auth.displayName = extra.displayName
  }
  if (typeof extra.remainIntegral === 'number') {
    profile.auth.remainIntegral = extra.remainIntegral
  }

  saveProfiles(profiles)
  saveActiveProfileIndex(targetIndex)

  // 同时保存到全局 auth（向后兼容）
  saveAuth({ isLoggedIn: true, loginName, userId: userId || loginName, sesId })
}

// ==================== 方法 ====================
/** 协议勾选状态变化 */
function onAgreementChange(e) {
  agreed.value = e.detail.value.includes('1')
}

/** 打开协议/隐私政策页面 */
function openAgreement(type) {
  uni.navigateTo({ url: `/pages/agreement/agreement?type=${type}` })
}

/**
 * 初始化页面：检查是否有已登录的 Profile。
 *
 * 由主页面某个"空账号槽位"跳转而来时（targetSlotIndex >= 0），
 * 说明用户是要给新槽位登录，不能直接跳回主页，必须停留在此页输入账号。
 */
async function initPage() {
  const profiles = loadProfiles()
  const hasLoggedInProfile = profiles.some(p => p.auth && p.auth.isLoggedIn && p.auth.loginName && p.auth.sesId)

  // 目标是给某个空槽位登录：即使已有其他账号登录，也要停留本页
  if (targetSlotIndex >= 0) {
    const slot = profiles[targetSlotIndex]
    const slotLoggedIn = Boolean(slot && slot.auth && slot.auth.isLoggedIn && slot.auth.loginName && slot.auth.sesId)
    if (!slotLoggedIn) {
      await refreshCaptcha()
      return
    }
    // 该槽位已登录，直接回主页
    uni.redirectTo({ url: `/pages/main/main?slot=${targetSlotIndex}` })
    return
  }

  if (hasLoggedInProfile) {
    uni.redirectTo({ url: '/pages/main/main' })
    return
  }
  await refreshCaptcha()
}

/**
 * 刷新图形验证码：从接口获取验证码数据，解码为图片文件并显示
 */
async function refreshCaptcha() {
  loadingCaptcha.value = true
  captchaImage.value = ''
  try {
    const data = await getCaptchaU067()
    captchaData.value = data

    const imagePath = await decodeCaptchaImage(data)
    captchaImage.value = imagePath
  } catch (error) {
    console.error('[captcha] refreshCaptcha error:', error)
    uni.showModal({
      title: '获取验证码失败',
      content: error.message || '未知错误',
      showCancel: false
    })
  } finally {
    loadingCaptcha.value = false
  }
}

/** 切换到短信验证码登录模式 */
function switchToSms() {
  loginMode.value = 'sms'
}

/** 验证码图片加载成功回调 */
function onImageLoadSuccess(e) {
  console.log('[captcha] 图片引擎加载成功！尺寸:', e.detail.width, e.detail.height)
}

/** 验证码图片渲染失败时的错误处理与提示 */
function onCaptchaImageError(e) {
  console.error('[captcha] image render error', {
    err: e,
    errMsg: e.detail ? e.detail.errMsg : (e.errMsg || JSON.stringify(e)),
    srcPrefix: String(captchaImage.value || '').slice(0, 80),
    srcLength: String(captchaImage.value || '').length
  })
  uni.showToast({ title: '验证码图片渲染失败，请重试', icon: 'none' })
}

/**
 * 启动倒计时（默认 60 秒），每秒更新 smsCountdown
 * @param {number} seconds - 倒计时总秒数，默认 60
 */
function startCountdown(seconds = 60) {
  smsCountdown.value = seconds
  countdownTimer = setInterval(() => {
    smsCountdown.value--
    if (smsCountdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

/**
 * 发送短信验证码：校验手机号与图形验证码后调用发短信接口
 * 发送成功后启动 60 秒倒计时，防止重复发送
 */
async function handleSendSms() {
  if (!phone.value) {
    uni.showToast({ title: '请先输入手机号', icon: 'none' })
    return
  }
  if (!captchaCode.value) {
    uni.showToast({ title: '请先输入图形验证码', icon: 'none' })
    return
  }
  if (!captchaData.value) {
    uni.showToast({ title: '请先获取图形验证码', icon: 'none' })
    return
  }

  sendingSms.value = true
  try {
    const result = await sendSms(captchaData.value, phone.value.trim(), captchaCode.value.trim())
    // 检查响应结果，result 为 '0' 表示成功
    if (!result || result.result !== '0') {
      uni.showToast({ title: (result && result.msg) || '短信发送失败', icon: 'none' })
      return
    }
    uni.showToast({ title: '短信验证码已发送', icon: 'success' })
    startCountdown()
  } catch (error) {
    uni.showToast({ title: error.message || '短信发送失败', icon: 'none' })
  } finally {
    sendingSms.value = false
  }
}

/**
 * 提交登录：根据当前登录模式调用密码登录或短信登录接口
 * 登录成功后将 loginName / userId / sesId 保存到本地存储，然后跳转主页
 */
async function submitLogin() {
  // 测试账号: admin/admin 直接跳过登录
  if (loginMode.value === 'password' && phone.value.trim() === 'admin' && password.value === 'admin') {
    if (!agreed.value) {
      uni.showToast({ title: '请先同意用户服务协议和隐私政策', icon: 'none' })
      return
    }
    saveLoginToProfile('admin', 'admin', 'test_ses_id', { displayName: '测试管理员', remainIntegral: 999 })
    uni.showToast({ title: '测试登录成功', icon: 'success' })
    setTimeout(() => {
      const slotQuery = targetSlotIndex >= 0 ? `?slot=${targetSlotIndex}` : ''
      uni.redirectTo({ url: `/pages/main/main${slotQuery}` })
    }, 300)
    return
  }

  if (!agreed.value) {
    uni.showToast({ title: '请先同意用户服务协议和隐私政策', icon: 'none' })
    return
  }

  if (!phone.value) {
    uni.showToast({ title: '请输入手机号', icon: 'none' })
    return
  }
  if (!captchaCode.value) {
    uni.showToast({ title: '请输入图形验证码', icon: 'none' })
    return
  }
  if (!captchaData.value) {
    uni.showToast({ title: '请先获取图形验证码', icon: 'none' })
    return
  }

  // 根据不同登录模式校验必填字段
  if (loginMode.value === 'password') {
    if (!password.value) {
      uni.showToast({ title: '请输入密码', icon: 'none' })
      return
    }
  } else {
    if (!smsCode.value) {
      uni.showToast({ title: '请输入短信验证码', icon: 'none' })
      return
    }
  }

  submitting.value = true
  try {
    let result
    // 密码登录：使用 U004 接口（含图形验证码校验）
    if (loginMode.value === 'password') {
      result = await loginU004WithCode(
        captchaData.value,
        phone.value.trim(),
        password.value,
        captchaCode.value.trim()
      )
    } else {
      // 短信验证码登录：使用 U065 接口
      result = await loginU065(phone.value.trim(), smsCode.value.trim())
    }

    // 检查登录响应是否成功
    if (!result || result.result !== '0') {
      uni.showToast({ title: (result && result.msg) || '登录失败', icon: 'none' })
      await refreshCaptcha()
      return
    }

    // 从登录响应中提取用户身份信息
    const loginName = result.login_name || result.user_id || ''
    const userId = result.user_id || loginName
    const sesId = result.ses_id || ''

    if (!loginName || !sesId) {
      uni.showToast({ title: '登录响应缺少 login_name 或 ses_id', icon: 'none' })
      await refreshCaptcha()
      return
    }

    // 登录响应里若带真实姓名/积分，一并写入该账号
    const displayName = result.name || result.sensitive_name || ''
    const integral = parseInt(result.remain_integral)
    const extra = {}
    if (displayName) extra.displayName = displayName
    if (Number.isFinite(integral)) extra.remainIntegral = integral

    // 保存登录态到目标账号槽位
    saveLoginToProfile(loginName, userId, sesId, extra)

    uni.showToast({ title: '登录成功', icon: 'success' })
    // 延迟跳转以显示 Toast；带上槽位参数，让主页选中刚登录的账号
    setTimeout(() => {
      const slotQuery = targetSlotIndex >= 0 ? `?slot=${targetSlotIndex}` : ''
      uni.redirectTo({ url: `/pages/main/main${slotQuery}` })
    }, 300)
  } catch (error) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
    await refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

// ==================== 生命周期 ====================
/** 页面加载时初始化，检查登录态并加载验证码 */
onLoad((options) => {
  // 记录由主页面某个账号槽位指定的目标位置
  if (options && options.slot !== undefined && options.slot !== '') {
    const parsed = Number(options.slot)
    if (Number.isFinite(parsed) && parsed >= 0) {
      targetSlotIndex = parsed
    }
  }
  initPage()
})
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
  margin-bottom: 24rpx;
  font-size: 24rpx;
  color: #5f6368;
}

/* ---------- 卡片 ---------- */
.card {
  background: #fff;
  border-radius: 28rpx;
  padding: 36rpx 32rpx;
  box-shadow: 0 1rpx 3rpx rgba(60,64,67,.15), 0 4rpx 8rpx 2rpx rgba(60,64,67,.06);
}

/* ---------- 品牌标识 ---------- */
.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28rpx;
}

.brand-mark {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  background: #1a73e8;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18rpx;
  box-shadow: 0 4rpx 10rpx rgba(26, 115, 232, 0.35);
}

.brand-mark-text {
  font-size: 44rpx;
  font-weight: 700;
  color: #fff;
}

.title {
  font-size: 34rpx;
  font-weight: 600;
  color: #1f1f1f;
  letter-spacing: 0.3rpx;
}

.subtitle {
  font-size: 24rpx;
  color: #5f6368;
  margin-top: 8rpx;
}

/* ---------- Material 3 分段按钮 ---------- */
.segmented {
  display: flex;
  background: #f1f3f4;
  border: 1.5rpx solid #dadce0;
  border-radius: 9999rpx;
  padding: 5rpx;
  margin-bottom: 32rpx;
}

.seg-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 26rpx;
  font-weight: 500;
  color: #444746;
  border-radius: 9999rpx;
  transition: all 0.2s ease;
}

.seg-item.active {
  background: #fff;
  color: #1a73e8;
  font-weight: 600;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 1rpx 3rpx rgba(60,64,67,.15);
}

/* ---------- 表单字段 ---------- */
.field {
  margin-bottom: 22rpx;
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
  height: 92rpx;
  border: 1.5rpx solid #dadce0;
  border-radius: 16rpx;
  padding: 0 22rpx;
  box-sizing: border-box;
  background: #fff;
  font-size: 28rpx;
  color: #1f1f1f;
}

/* ---------- 验证码行 ---------- */
.captcha-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.captcha-frame {
  flex: 1;
  height: 92rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border: 1.5rpx solid #dadce0;
  border-radius: 12rpx;
  overflow: hidden;
}

.captcha-img {
  width: 100%;
  height: 92rpx;
  display: block;
}

.captcha-placeholder {
  color: #5f6368;
  font-size: 22rpx;
}

/* ---------- 短信验证码行 ---------- */
.sms-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.sms-input {
  flex: 1;
}

/* ---------- 按钮 ---------- */
.btn {
  height: 88rpx;
  border-radius: 9999rpx;
  font-size: 28rpx;
  font-weight: 600;
  letter-spacing: 0.4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.btn-primary {
  width: 100%;
  margin-top: 12rpx;
  background: #1a73e8;
  color: #fff;
  box-shadow: 0 1rpx 2rpx rgba(60,64,67,.30), 0 2rpx 6rpx 2rpx rgba(60,64,67,.15);
}

.btn-outline {
  background: transparent;
  color: #1a73e8;
  border: 1.5rpx solid #dadce0;
}

.btn-refresh {
  width: 132rpx;
  flex-shrink: 0;
  height: 92rpx;
  font-size: 26rpx;
  padding: 0;
}

.btn-sms {
  width: 240rpx;
  flex-shrink: 0;
  font-size: 26rpx;
}

.btn-sms[disabled] {
  color: rgba(60, 64, 67, 0.38);
  background: rgba(60, 64, 67, 0.06);
}

.btn[disabled] {
  color: #fff;
  background: rgba(0, 0, 0, 0.12) !important;
  border-color: transparent !important;
  box-shadow: none;
  opacity: 0.6;
}

.btn-outline[disabled] {
  color: rgba(60, 64, 67, 0.38) !important;
  background: rgba(60, 64, 67, 0.06) !important;
  border-color: #dadce0 !important;
}

/* ---------- 协议行 ---------- */
.agreement-row {
  display: flex;
  align-items: flex-start;
  margin-top: 28rpx;
}

.agreement-text {
  font-size: 24rpx;
  color: #5f6368;
  line-height: 1.6;
  margin-left: 8rpx;
  flex: 1;
}

.link {
  color: #1a73e8;
  font-weight: 500;
}
</style>
