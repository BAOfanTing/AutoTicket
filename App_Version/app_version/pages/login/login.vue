<template>
  <view class="page">
    <view class="card">
      <view class="title">账号登录</view>

      <view class="field">
        <text class="label">手机号</text>
        <input v-model="phone" class="input" placeholder="请输入手机号" />
      </view>

      <view class="field">
        <text class="label">密码</text>
        <input v-model="password" class="input" password placeholder="请输入密码" />
      </view>

      <view class="field">
        <text class="label">验证码</text>
        <view class="captcha-row"
          style="display: flex; align-items: center; justify-content: center; background: #eee; padding: 10rpx;">
          <image v-if="captchaImage" :src="captchaImage" :key="captchaImage" mode="scaleToFill"
            style="width: 240rpx; height: 100rpx; display: block; background-color: #fff; border: 2rpx solid red;"
            @error="onCaptchaImageError" @load="onImageLoadSuccess" />
          <view v-else>正在渲染...</view>
          <button class="btn btn-ghost" @click="refreshCaptcha" :disabled="loadingCaptcha">
            {{ loadingCaptcha ? '获取中...' : '刷新验证码' }}
          </button>
        </view>
      </view>

      <view class="field">
        <text class="label">输入验证码</text>
        <input v-model="captchaCode" class="input" placeholder="请输入验证码" />
      </view>

      <button class="btn btn-primary" @click="submitLogin" :disabled="submitting">
        {{ submitting ? '登录中...' : '登录' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { decodeCaptchaImage, getCaptchaU067, loginU004WithCode } from '../../src/services/authService'
import { loadAuth, saveAuth } from '../../src/utils/storage'

// ==================== 状态 ====================
const phone = ref('')
const password = ref('')
const captchaCode = ref('')
const captchaImage = ref('')
const captchaData = ref(null)
const loadingCaptcha = ref(false)
const submitting = ref(false)

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

function onImageLoadSuccess(e) {
  console.log('[captcha] 图片引擎加载成功！尺寸:', e.detail.width, e.detail.height)
}

function onCaptchaImageError(e) {
  console.log('[captcha] image render error', {
    err: e,
    srcPrefix: String(captchaImage.value || '').slice(0, 80),
    srcLength: String(captchaImage.value || '').length
  })
  uni.showToast({ title: '验证码图片渲染失败，请重试', icon: 'none' })
}

async function submitLogin() {
  if (!phone.value || !password.value || !captchaCode.value) {
    uni.showToast({ title: '手机号、密码、验证码都必须填写', icon: 'none' })
    return
  }
  if (!captchaData.value) {
    uni.showToast({ title: '请先获取验证码', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const result = await loginU004WithCode(
      captchaData.value,
      phone.value.trim(),
      password.value,
      captchaCode.value.trim()
    )

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
}

.field {
  margin-bottom: 20rpx;
}

.label {
  display: block;
  margin-bottom: 10rpx;
  color: #6e6e73;
}

.input {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #d2d2d7;
  border-radius: 14rpx;
  padding: 0 20rpx;
  box-sizing: border-box;
  background: #fff;
}

.captcha-row {
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.captcha {
  flex: 1;
  height: 90rpx;
  border: 1rpx solid #d2d2d7;
  border-radius: 12rpx;
  background: #fff;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 24rpx;
}

.btn {
  height: 80rpx;
  border-radius: 14rpx;
  font-size: 28rpx;
}

.btn-primary {
  background: #007aff;
  color: #fff;
}

.btn-ghost {
  width: 220rpx;
  background: #f5f5f7;
  color: #1d1d1f;
}
</style>
