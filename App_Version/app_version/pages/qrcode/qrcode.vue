<template>
  <view class="page">
    <view class="card" v-if="loading">
      <view class="loading-text">正在获取绿色出行码...</view>
    </view>

    <view class="card" v-else-if="error">
      <view class="error-text">{{ error }}</view>
      <button class="btn btn-primary" @click="fetchQrCode">重试</button>
    </view>

    <template v-else>
      <view class="card qr-card">
        <canvas canvas-id="qrCanvas" class="qr-canvas"></canvas>
      </view>

      <view class="card info-card">
        <view class="info-row">
          <text class="info-label">余额</text>
          <text class="info-value money">{{ money }} 元</text>
        </view>
        <view class="info-row">
          <text class="info-label">交通卡号</text>
          <text class="info-value">{{ cardNo }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">有效期</text>
          <text class="info-value">{{ deadline }}</text>
        </view>
      </view>

      <view class="actions">
        <button class="btn btn-close" @click="goBack">关闭</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { loadAuth } from '../../src/utils/storage'
import { getGreenTravelCode } from '../../src/services/qrService'
import UQRCode from 'uqrcodejs'

const loading = ref(true)
const error = ref('')
const money = ref('0')
const cardNo = ref('')
const deadline = ref('')

function formatDeadtime(ts) {
  if (!ts) return ''
  const date = new Date(Number(ts) * 1000)
  const y = date.getFullYear()
  const M = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${M}-${d} ${h}:${m}:${s}`
}

async function fetchQrCode() {
  const auth = loadAuth()
  if (!auth || !auth.isLoggedIn || !auth.loginName || !auth.sesId) {
    error.value = '登录状态已失效，请重新登录'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  try {
    const data = await getGreenTravelCode(auth.loginName, auth.sesId)
    if (!data || !data.qrcode) {
      throw new Error('获取乘车码数据为空')
    }
    money.value = data.money || '0'
    cardNo.value = data.trafficCardNo || ''
    deadline.value = formatDeadtime(data.deadTime)

    await nextTick()
    const qr = new UQRCode()
    qr.data = data.qrcode
    qr.size = 280
    qr.make()
    const ctx = uni.createCanvasContext('qrCanvas')
    qr.canvasContext = ctx
    qr.drawCanvas()
  } catch (e) {
    error.value = e.message || '获取绿色出行码失败'
  } finally {
    loading.value = false
  }
}

function goBack() {
  uni.navigateBack()
}

onMounted(() => {
  fetchQrCode()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 24rpx;
  width: 100%;
  box-sizing: border-box;
}

.loading-text {
  text-align: center;
  color: #6e6e73;
  font-size: 28rpx;
  padding: 40rpx 0;
}

.error-text {
  text-align: center;
  color: #d93025;
  font-size: 28rpx;
  padding: 20rpx 0;
  margin-bottom: 20rpx;
}

.qr-card {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
}

.qr-canvas {
  width: 560rpx;
  height: 560rpx;
}

.info-card {
  padding: 24rpx 30rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 28rpx;
  color: #6e6e73;
}

.info-value {
  font-size: 28rpx;
  color: #1d1d1f;
  font-weight: 500;
}

.money {
  color: #ff9500;
  font-size: 32rpx;
  font-weight: 700;
}

.actions {
  width: 100%;
  margin-top: 10rpx;
}

.btn {
  border-radius: 14rpx;
  font-size: 28rpx;
  height: 80rpx;
  line-height: 80rpx;
}

.btn-primary {
  background: #007aff;
  color: #fff;
}

.btn-close {
  background: #f5f5f7;
  color: #1d1d1f;
}
</style>
