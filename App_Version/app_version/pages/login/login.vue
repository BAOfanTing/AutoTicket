<template>
  <view class="page">
    <view class="hero">
      <image class="hero-image" src="../../resouse/login.jpg" mode="widthFix" />
    </view>

    <view class="card">
      <view class="title">杭工e家</view>

      <!-- 登录方式切换 -->
      <view class="mode-tabs">
        <text
          class="mode-tab"
          :class="{ active: loginMode === 'password' }"
          @click="loginMode = 'password'"
        >密码登录</text>
        <text
          class="mode-tab"
          :class="{ active: loginMode === 'sms' }"
          @click="switchToSms"
        >短信验证码登录</text>
      </view>

      <!-- 手机号（共用） -->
      <view class="field">
        <text class="label">手机号</text>
        <input v-model="phone" class="input" placeholder="请输入手机号" />
      </view>

      <!-- 密码登录字段 -->
      <template v-if="loginMode === 'password'">
        <view class="field">
          <text class="label">密码</text>
          <input v-model="password" class="input" password placeholder="请输入密码" />
        </view>
      </template>

      <!-- 验证码（共用） -->
      <view class="field">
        <text class="label">图形验证码</text>
        <view class="captcha-row">
          <image v-if="captchaImage" :src="captchaImage" :key="captchaImage" mode="scaleToFill"
            style="width: 240rpx; height: 100rpx; display: block; background-color: #fff; border: 2rpx solid #ddd; border-radius: 8rpx;"
            @error="onCaptchaImageError" @load="onImageLoadSuccess" />
          <view v-else class="captcha-placeholder">正在渲染...</view>
          <button class="btn btn-ghost" @click="refreshCaptcha" :disabled="loadingCaptcha">
            {{ loadingCaptcha ? '获取中...' : '刷新验证码' }}
          </button>
        </view>
      </view>

      <view class="field">
        <text class="label">输入验证码</text>
        <input v-model="captchaCode" class="input" placeholder="请输入图形验证码" />
      </view>

      <!-- 短信验证码登录额外字段 -->
      <template v-if="loginMode === 'sms'">
        <view class="field">
          <text class="label">短信验证码</text>
          <view class="sms-row">
            <input v-model="smsCode" class="input sms-input" placeholder="请输入短信验证码" />
            <button
              class="btn btn-sms"
              :disabled="sendingSms || smsCountdown > 0"
              @click="handleSendSms"
            >
              {{ smsCountdown > 0 ? `${smsCountdown}s` : (sendingSms ? '发送中...' : '获取验证码') }}
            </button>
          </view>
        </view>
      </template>

      <button class="btn btn-primary" @click="submitLogin" :disabled="submitting">
        {{ submitting ? '登录中...' : '登录' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { decodeCaptchaImage, getCaptchaU067, loginU004WithCode, sendSms, loginU065 } from '../../src/services/authService'
import { loadAuth, saveAuth } from '../../src/utils/storage'

// ==================== 状态 ====================
const loginMode = ref('password')
const phone = ref('')
const password = ref('')
const captchaCode = ref('')
const captchaImage = ref('')
const captchaData = ref(null)
const loadingCaptcha = ref(false)
const submitting = ref(false)

// 短信登录相关
const smsCode = ref('')
const sendingSms = ref(false)
const smsCountdown = ref(0)
let countdownTimer = null

// ==================== 方法 ====================
async function initPage() {
  const auth = loadAuth()
  if (auth && auth.isLoggedIn && auth.loginName && auth.sesId) {
    uni.redirectTo({ url: '/pages/main/main' })
    return
  }
  await refreshCaptcha()
}

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

function switchToSms() {
  loginMode.value = 'sms'
  // 短信登录不需要密码，清除密码字段校验
}

function onImageLoadSuccess(e) {
  console.log('[captcha] 图片引擎加载成功！尺寸:', e.detail.width, e.detail.height)
}

function onCaptchaImageError(e) {
  console.error('[captcha] image render error', {
    err: e,
    errMsg: e.detail ? e.detail.errMsg : (e.errMsg || JSON.stringify(e)),
    srcPrefix: String(captchaImage.value || '').slice(0, 80),
    srcLength: String(captchaImage.value || '').length
  })
  uni.showToast({ title: '验证码图片渲染失败，请重试', icon: 'none' })
}

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

async function submitLogin() {
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
    if (loginMode.value === 'password') {
      result = await loginU004WithCode(
        captchaData.value,
        phone.value.trim(),
        password.value,
        captchaCode.value.trim()
      )
    } else {
      result = await loginU065(phone.value.trim(), smsCode.value.trim())
    }

    if (!result || result.result !== '0') {
      uni.showToast({ title: (result && result.msg) || '登录失败', icon: 'none' })
      await refreshCaptcha()
      return
    }

    const loginName = result.login_name || result.user_id || ''
    const userId = result.user_id || loginName
    const sesId = result.ses_id || ''

    if (!loginName || !sesId) {
      uni.showToast({ title: '登录响应缺少 login_name 或 ses_id', icon: 'none' })
      await refreshCaptcha()
      return
    }

    saveAuth({
      isLoggedIn: true,
      loginName,
      userId,
      sesId
    })

    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/main/main' })
    }, 300)
  } catch (error) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
    await refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

// ==================== 生命周期 ====================
onLoad(() => {
  initPage()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  box-sizing: border-box;
}

.hero {
  margin-bottom: 24rpx;
}

.hero-image {
  display: block;
  width: 100%;
  border-radius: 20rpx;
}

.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.title {
  font-size: 36rpx;
  font-weight: 700;
  margin-bottom: 24rpx;
  text-align: center;
}

/* 登录方式切换标签 */
.mode-tabs {
  display: flex;
  margin-bottom: 28rpx;
  border-bottom: 2rpx solid #e5e5e5;
}

.mode-tab {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #8e8e93;
  position: relative;
  cursor: pointer;
}

.mode-tab.active {
  color: #007aff;
  font-weight: 600;
}

.mode-tab.active::after {
  content: '';
  position: absolute;
  bottom: -2rpx;
  left: 10%;
  width: 80%;
  height: 4rpx;
  background: #007aff;
  border-radius: 2rpx;
}

.field {
  margin-bottom: 20rpx;
}

.label {
  display: block;
  margin-bottom: 10rpx;
  color: #6e6e73;
  font-size: 26rpx;
}

.input {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #d2d2d7;
  border-radius: 14rpx;
  padding: 0 20rpx;
  box-sizing: border-box;
  background: #fff;
  font-size: 28rpx;
}

.captcha-row {
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.captcha-placeholder {
  width: 240rpx;
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f7;
  border-radius: 8rpx;
  color: #999;
  font-size: 24rpx;
}

/* 短信验证码行 */
.sms-row {
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.sms-input {
  flex: 1;
}

.btn {
  height: 80rpx;
  border-radius: 14rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  width: 100%;
  margin-top: 12rpx;
  background: #007aff;
  color: #fff;
}

.btn-ghost {
  width: 220rpx;
  background: #f5f5f7;
  color: #1d1d1f;
  font-size: 26rpx;
}

.btn-sms {
  width: 220rpx;
  background: #f5f5f7;
  color: #007aff;
  font-size: 26rpx;
  flex-shrink: 0;
}

.btn-sms[disabled] {
  color: #c0c0c0;
}
</style>
