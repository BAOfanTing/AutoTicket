<template>
  <view class="page">
    <view class="card">
      <view class="title">
        <text class="title-text">{{ title }}</text>
      </view>
      <scroll-view scroll-y class="content-box">
        <view class="section" v-for="(section, idx) in sections" :key="idx">
          <view class="section-title" v-if="section.title">{{ section.title }}</view>
          <view class="section-body">{{ section.body }}</view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const title = ref('')
const sections = ref([])

const userAgreement = {
  title: '用户服务协议',
  sections: [
    {
      title: '一、协议范围',
      body: '本协议是您与 AutoTicket 之间关于使用本小程序服务所订立的协议。请您仔细阅读本协议，如您不同意本协议任何条款，请勿使用本服务。'
    },
    {
      title: '二、服务内容',
      body: '本小程序为用户提供 e 家 APP 相关的自动化辅助工具服务，包括登录状态管理、每日任务执行、积分展示及优惠券信息展示等功能。'
    },
    {
      title: '三、账号与登录',
      body: '您可以使用手机号登录本小程序。登录过程中我们需要收集您的手机号、短信验证码或登录凭证信息，仅用于完成登录及后续服务功能，不会用于其他目的。'
    },
    {
      title: '四、用户行为规范',
      body: '您承诺使用本服务时遵守相关法律法规及平台规则，不得将本服务用于任何违法违规、侵犯他人权益或破坏平台秩序的用途。'
    },
    {
      title: '五、免责声明',
      body: '本小程序按“原样”提供，开发者对因网络、第三方平台政策调整或用户不当使用导致的损失不承担责任。'
    },
    {
      title: '六、协议变更',
      body: '开发者有权根据需要修改本协议，修改后的协议将在小程序内公布，您继续使用本服务即视为同意修改后的协议。'
    }
  ]
}

const privacyPolicy = {
  title: '隐私政策',
  sections: [
    {
      title: '一、我们收集的信息',
      body: '为提供服务，我们可能需要收集您的手机号、短信验证码、登录凭证（login_name、ses_id 等）以及设备相关信息。上述信息仅在您主动授权并提供的情况下收集。'
    },
    {
      title: '二、信息使用目的',
      body: '我们使用您的信息用于：完成登录验证、维持登录会话、执行您主动发起的每日任务及查询操作、向您展示积分及优惠券信息。'
    },
    {
      title: '三、信息存储与保护',
      body: '您的登录凭证仅存储在小程序本地缓存中，不会上传至我们的服务器。我们会采取合理措施保护您的信息安全，但请您妥善保管自己的账号信息。'
    },
    {
      title: '四、信息共享与披露',
      body: '我们不会将您的个人信息出售、出租或以其他方式非法提供给第三方，除非获得您的明确同意或法律法规另有要求。'
    },
    {
      title: '五、您的权利',
      body: '您可以随时退出登录，我们将清除本地保存的登录信息。您也可以联系开发者了解您的信息处理情况。'
    },
    {
      title: '六、政策更新',
      body: '我们可能会根据服务变化更新本隐私政策，更新后的政策将在小程序内公布，继续使用即视为同意更新后的政策。'
    }
  ]
}

onLoad((options) => {
  const type = options.type || 'user'
  const data = type === 'privacy' ? privacyPolicy : userAgreement
  title.value = data.title
  sections.value = data.sections
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

.card {
  background: #fff;
  border-radius: 28rpx;
  padding: 32rpx;
  box-shadow: 0 1rpx 3rpx rgba(60,64,67,.15), 0 4rpx 8rpx 2rpx rgba(60,64,67,.06);
}

.title {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 28rpx;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid #e8eaed;
}

.title-text {
  font-size: 34rpx;
  font-weight: 600;
  color: #1f1f1f;
  letter-spacing: 0.3rpx;
}

.content-box {
  max-height: calc(100vh - 200rpx);
}

.section {
  margin-bottom: 26rpx;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #1f1f1f;
  margin-bottom: 12rpx;
}

.section-title::before {
  content: '';
  width: 6rpx;
  height: 26rpx;
  background: #1a73e8;
  border-radius: 9999rpx;
}

.section-body {
  font-size: 27rpx;
  color: #444746;
  line-height: 1.8;
  text-align: justify;
}
</style>
