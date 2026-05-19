<template>
  <view class="page">
    <!-- 加载中的提示 -->
    <view class="card" v-if="loading">
      <view class="loading-text">正在获取绿色出行码...</view>
    </view>

    <!-- 获取失败时显示错误信息和重试按钮 -->
    <view class="card" v-else-if="error">
      <view class="error-text">{{ error }}</view>
      <button class="btn btn-primary" @click="fetchQrCode">重试</button>
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
        <view class="info-row">
          <text class="info-label">可用张数</text>
          <text class="info-value">{{ subwayInfo.useNum }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">2元券</text>
          <text class="info-value">{{ subwayInfo.num2 }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">4元券</text>
          <text class="info-value">{{ subwayInfo.num4 }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">6元券</text>
          <text class="info-value">{{ subwayInfo.num6 }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">即将过期</text>
          <text class="info-value">{{ subwayInfo.expireNum }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">记录总数</text>
          <text class="info-value">{{ subwayInfo.totalCount }}</text>
        </view>

        <view v-if="subwayInfo.list.length" class="coupon-list">
          <view class="coupon-item" v-for="(item, index) in subwayInfo.list" :key="index">
            <view class="coupon-line">
              <text class="coupon-label">券信息</text>
              <text class="coupon-value">{{ item.award_name || item.awardTypeName || item.award_type || '-' }}</text>
            </view>
            <view class="coupon-line">
              <text class="coupon-label">状态</text>
              <text class="coupon-value">{{ item.use_state_name || item.useStateName || item.use_state || '-' }}</text>
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
        <button class="btn btn-close" @click="goBack">关闭</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { loadAuth } from '../../src/utils/storage'
import { getGreenTravelCode, getSubwayTicketRecords } from '../../src/services/qrService'

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
/** 地铁优惠券查询结果 */
const subwayInfo = ref({
  useNum: '0',
  num2: '0',
  num4: '0',
  num6: '0',
  expireNum: '0',
  totalCount: '0',
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
 * 获取绿色出行二维码并查询地铁优惠券统计
 */
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
    const [qrData, subwayData] = await Promise.all([
      getGreenTravelCode(auth.loginName, auth.sesId),
      getSubwayTicketRecords(auth.loginName, auth.sesId)
    ])

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

    subwayInfo.value = {
      useNum: subwayData.use_num || '0',
      num2: subwayData.num_2 || '0',
      num4: subwayData.num_4 || '0',
      num6: subwayData.num_6 || '0',
      expireNum: subwayData.expire_num || '0',
      totalCount: subwayData.total_count || '0',
      list: Array.isArray(subwayData.list) ? subwayData.list : []
    }
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

.title {
  font-size: 34rpx;
  font-weight: 700;
  margin-bottom: 20rpx;
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

.qr-image {
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

.coupon-list {
  margin-top: 20rpx;
}

.coupon-item {
  padding: 20rpx 0;
  border-top: 1rpx solid #f0f0f0;
}

.coupon-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.coupon-label {
  font-size: 24rpx;
  color: #8e8e93;
}

.coupon-value {
  font-size: 24rpx;
  color: #1d1d1f;
}

.empty-text {
  margin-top: 20rpx;
  text-align: center;
  color: #8e8e93;
  font-size: 26rpx;
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
