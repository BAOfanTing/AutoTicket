<template>
  <view class="page">
    <!-- 加载中的提示 -->
    <view class="card" v-if="loading">
      <view class="loading-text">正在获取绿色出行码...</view>
    </view>

    <!-- 获取失败时显示错误信息和重试按钮 -->
    <view class="card" v-else-if="error">
      <view class="error-icon">!</view>
      <view class="error-text">{{ error }}</view>
      <button class="btn btn-primary btn-retry" @click="fetchQrCode">重试</button>
    </view>

    <template v-else>
      <!-- 服务端渲染的二维码图片 -->
      <view class="card qr-card">
        <image :src="qrImage" class="qr-image" mode="aspectFit" />
      </view>

      <!-- 余额与交通卡信息卡片 -->
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

      <!-- 地铁优惠券查询结果 -->
      <view class="card info-card">
        <view class="title">地铁优惠券</view>
        <view class="coupon-switches">
          <view
            class="coupon-chip"
            :class="{ active: activeAwardType === '1' }"
            @click="switchAwardType('1')"
          >
            <text class="coupon-chip-label">2元券</text>
            <text class="coupon-chip-num">{{ subwayInfo.num2 }}</text>
          </view>
          <view
            class="coupon-chip"
            :class="{ active: activeAwardType === '2' }"
            @click="switchAwardType('2')"
          >
            <text class="coupon-chip-label">4元券</text>
            <text class="coupon-chip-num">{{ subwayInfo.num4 }}</text>
          </view>
          <view
            class="coupon-chip"
            :class="{ active: activeAwardType === '3' }"
            @click="switchAwardType('3')"
          >
            <text class="coupon-chip-label">6元券</text>
            <text class="coupon-chip-num">{{ subwayInfo.num6 }}</text>
          </view>
        </view>

        <view v-if="subwayInfo.list.length" class="coupon-list">
          <view class="coupon-item" v-for="(item, index) in subwayInfo.list" :key="index">
            <view class="coupon-line">
              <text class="coupon-label">券名称</text>
              <text class="coupon-value">{{ item.exchange_name || item.award_name || item.awardTypeName || item.award_type || '-' }}</text>
            </view>
            <view class="coupon-line" v-if="item.create_time || item.createTime">
              <text class="coupon-label">领取时间</text>
              <text class="coupon-value">{{ item.create_time || item.createTime }}</text>
            </view>
            <view class="coupon-line" v-if="item.expire_time || item.expireTime">
              <text class="coupon-label">过期时间</text>
              <text class="coupon-value">{{ item.expire_time || item.expireTime }}</text>
            </view>
          </view>
        </view>
        <view v-else class="empty-text">暂无优惠券记录</view>
      </view>

      <!-- 关闭按钮 -->
      <view class="actions">
        <button class="btn btn-outline" @click="goBack">关闭</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { loadProfiles, loadActiveProfileIndex } from '../../src/utils/storage'
import { getGreenTravelCode, getSubwayTicketRecords } from '../../src/services/qrService'

// ==================== 工具 ====================
/** 获取当前选中 Profile 的登录态 */
function getCurrentAuth() {
  const profiles = loadProfiles()
  const idx = loadActiveProfileIndex()
  const p = profiles[idx]
  if (!p || !p.auth || !p.auth.isLoggedIn) return null
  return { loginName: p.auth.loginName, sesId: p.auth.sesId, userId: p.auth.userId }
}

// ==================== 响应式状态定义 ====================
/** 是否正在加载数据 */
const loading = ref(true)
/** 错误信息，为空表示无错误 */
const error = ref('')
/** 服务端返回的二维码图片 base64 */
const qrImage = ref('')
/** 交通卡余额 */
const money = ref('0')
/** 交通卡号 */
const cardNo = ref('')
/** 二维码有效期 */
const deadline = ref('')
const activeAwardType = ref('1')
/** 地铁优惠券查询结果 */
const subwayInfo = ref({
  num2: '0',
  num4: '0',
  num6: '0',
  list: []
})

// ==================== 方法 ====================

/**
 * 格式化时间戳为日期时间字符串
 * @param {string|number} ts - Unix 时间戳（秒）
 * @returns {string} 格式为 YYYY-MM-DD HH:mm:ss
 */
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

/**
 * 获取当前选中券类型的地铁优惠券统计与记录
 */
async function fetchSubwayInfo() {
  const auth = getCurrentAuth()
  if (!auth) {
    error.value = '登录状态已失效，请重新登录'
    return
  }
  const subwayData = await getSubwayTicketRecords(auth.loginName, auth.sesId, activeAwardType.value)

  subwayInfo.value = {
    num2: subwayData.num_2 || '0',
    num4: subwayData.num_4 || '0',
    num6: subwayData.num_6 || '0',
    list: Array.isArray(subwayData.list) ? subwayData.list : []
  }
}

/**
 * 切换优惠券类型并重新查询列表
 */
async function switchAwardType(type) {
  if (activeAwardType.value === type) return

  loading.value = true
  error.value = ''
  try {
    activeAwardType.value = type
    await fetchSubwayInfo()
  } catch (e) {
    error.value = e.message || '获取地铁优惠券失败'
  } finally {
    loading.value = false
  }
}

/**
 * 获取绿色出行二维码并查询地铁优惠券统计
 */
async function fetchQrCode() {
  const auth = getCurrentAuth()
  if (!auth) {
    error.value = '登录状态已失效，请重新登录'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  try {
    const qrData = await getGreenTravelCode(auth.loginName, auth.sesId)
	
    if (!qrData) {
      throw new Error('获取乘车码数据为空')
    }

    if (qrData.qrcodeImage) {
      qrImage.value = qrData.qrcodeImage.startsWith('data:')
        ? qrData.qrcodeImage
        : 'data:image/png;base64,' + qrData.qrcodeImage
    } else if (qrData.qrcode) {
      throw new Error('服务端未返回图片，请确认 isImage=1')
    } else {
      throw new Error('获取乘车码数据为空')
    }

    money.value = qrData.money || '0'
    cardNo.value = qrData.trafficCardNo || ''
    deadline.value = formatDeadtime(qrData.deadTime)

    await fetchSubwayInfo()
  } catch (e) {
    error.value = e.message || '获取绿色出行码失败'
  } finally {
    loading.value = false
  }
}

/** 返回上一页 */
function goBack() {
  uni.navigateBack()
}

// ==================== 生命周期 ====================
/** 组件挂载后自动获取绿色出行二维码 */
onMounted(() => {
  fetchQrCode()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  background: #f8f9fa;
  font-family: "Google Sans", "Roboto", -apple-system, "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

/* ---------- 通用卡片 ---------- */
.card {
  background: #fff;
  border-radius: 28rpx;
  padding: 30rpx;
  box-shadow: 0 1rpx 3rpx rgba(60,64,67,.15), 0 4rpx 8rpx 2rpx rgba(60,64,67,.06);
  margin-bottom: 24rpx;
  width: 100%;
  box-sizing: border-box;
}

.title {
  font-size: 28rpx;
  font-weight: 500;
  color: #1f1f1f;
  letter-spacing: 0.2rpx;
  margin-bottom: 22rpx;
}

.loading-text {
  text-align: center;
  color: #5f6368;
  font-size: 28rpx;
  padding: 40rpx 0;
}

/* ---------- 错误态 ---------- */
.error-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 9999rpx;
  background: rgba(217, 48, 37, 0.12);
  color: #d93025;
  font-size: 44rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20rpx;
}

.error-text {
  text-align: center;
  color: #d93025;
  font-size: 28rpx;
  padding: 0 20rpx 20rpx;
}

.btn-retry {
  width: 220rpx;
  margin: 0 auto;
}

/* ---------- 二维码卡片 ---------- */
.qr-card {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
}

.qr-image {
  width: 560rpx;
  height: 560rpx;
}

/* ---------- 信息卡片 ---------- */
.info-card {
  padding: 26rpx 30rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #e8eaed;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 28rpx;
  color: #5f6368;
}

.info-value {
  font-size: 28rpx;
  color: #1f1f1f;
  font-weight: 500;
}

.money {
  color: #f9ab00;
  font-size: 32rpx;
  font-weight: 700;
}

/* ---------- 优惠券切换 Chip ---------- */
.coupon-switches {
  display: flex;
  gap: 14rpx;
  margin-bottom: 8rpx;
}

.coupon-chip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  padding: 18rpx 0;
  border: 1.5rpx solid #dadce0;
  border-radius: 16rpx;
  background: #fff;
  transition: all 0.2s ease;
}

.coupon-chip-label {
  font-size: 24rpx;
  color: #5f6368;
  font-weight: 500;
}

.coupon-chip-num {
  font-size: 30rpx;
  color: #1f1f1f;
  font-weight: 700;
}

.coupon-chip.active {
  background: rgba(26, 115, 232, 0.08);
  border-color: #1a73e8;
}

.coupon-chip.active .coupon-chip-label,
.coupon-chip.active .coupon-chip-num {
  color: #1a73e8;
}

/* ---------- 优惠券列表 ---------- */
.coupon-list {
  margin-top: 20rpx;
}

.coupon-item {
  padding: 20rpx 0;
  border-top: 1rpx solid #e8eaed;
}

.coupon-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.coupon-label {
  font-size: 24rpx;
  color: #5f6368;
}

.coupon-value {
  font-size: 24rpx;
  color: #1f1f1f;
  font-weight: 500;
}

.empty-text {
  margin-top: 20rpx;
  text-align: center;
  color: #5f6368;
  font-size: 26rpx;
}

/* ---------- 按钮 ---------- */
.actions {
  width: 100%;
  margin-top: 8rpx;
}

.btn {
  width: 100%;
  border-radius: 9999rpx;
  font-size: 28rpx;
  font-weight: 600;
  letter-spacing: 0.4rpx;
  height: 88rpx;
  line-height: 88rpx;
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

.btn-outline {
  background: transparent;
  color: #1a73e8;
  border: 1.5rpx solid #dadce0;
}
</style>
