<template>
  <div class="subscription-page">
    <div class="container">
      <!-- Header -->
      <div class="page-header">
        <h1>Choose Your Plan</h1>
        <p class="subtitle">Unlock more features with our premium plans</p>
      </div>

      <!-- Current Plan Banner (if subscribed) -->
      <div v-if="currentPlan !== 'free'" class="current-plan-banner">
        <div class="banner-content">
          <span class="badge">Current Plan</span>
          <span class="plan-name">{{ getPlanName(currentPlan) }}</span>
          <span v-if="expiresAt" class="expires">
            Expires: {{ formatDate(expiresAt) }}
          </span>
        </div>
      </div>

      <!-- Success/Cancel Messages -->
      <div v-if="paymentSuccess" class="alert alert-success">
        Payment successful! Your plan has been upgraded to {{ getPlanName(currentPlan) }}.
      </div>
      <div v-if="paymentCancelled" class="alert alert-warning">
        Payment was cancelled. You can try again anytime.
      </div>

      <!-- Pricing Cards -->
      <div class="pricing-grid">
        <!-- Free Plan -->
        <div
          class="pricing-card"
          :class="{ active: currentPlan === 'free' }"
        >
          <div class="card-header">
            <h3>Free</h3>
            <div class="price">
              <span class="amount">$0</span>
              <span class="period">/month</span>
            </div>
          </div>
          <div class="card-body">
            <ul class="features">
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>5 voice profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>3 avatar profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>10 story generations/month</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Basic audiobook creation</span>
              </li>
              <li class="disabled">
                <svg viewBox="0 0 24 24" class="x-icon">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
                <span>Priority processing</span>
              </li>
              <li class="disabled">
                <svg viewBox="0 0 24 24" class="x-icon">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
                <span>HD video export</span>
              </li>
            </ul>
          </div>
          <div class="card-footer">
            <button
              v-if="currentPlan === 'free'"
              class="btn btn-current"
              disabled
            >
              Current Plan
            </button>
            <button
              v-else
              class="btn btn-secondary"
              disabled
            >
              Downgrade
            </button>
          </div>
        </div>

        <!-- Basic Plan -->
        <div
          class="pricing-card"
          :class="{ active: currentPlan === 'basic' }"
        >
          <div class="card-header">
            <h3>Basic</h3>
            <div class="price">
              <span class="amount">$9.9</span>
              <span class="period">/month</span>
            </div>
          </div>
          <div class="card-body">
            <ul class="features">
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>20 voice profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>10 avatar profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>50 story generations/month</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Unlimited audiobooks</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Priority processing</span>
              </li>
              <li class="disabled">
                <svg viewBox="0 0 24 24" class="x-icon">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
                <span>HD video export</span>
              </li>
            </ul>
          </div>
          <div class="card-footer">
            <button
              v-if="currentPlan === 'basic'"
              class="btn btn-current"
              disabled
            >
              Current Plan
            </button>
            <button
              v-else
              class="btn btn-primary"
              @click="openPaymentModal('basic')"
              :disabled="processingPayment"
            >
              {{ currentPlan === 'premium' ? 'Downgrade' : 'Upgrade' }}
            </button>
          </div>
        </div>

        <!-- Premium Plan -->
        <div
          class="pricing-card premium"
          :class="{ active: currentPlan === 'premium' }"
        >
          <div class="popular-badge">Most Popular</div>
          <div class="card-header">
            <h3>Premium</h3>
            <div class="price">
              <span class="amount">$19.9</span>
              <span class="period">/month</span>
            </div>
          </div>
          <div class="card-body">
            <ul class="features">
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Unlimited voice profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Unlimited avatar profiles</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Unlimited story generations</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Unlimited audiobooks</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>Priority processing</span>
              </li>
              <li>
                <svg viewBox="0 0 24 24" class="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
                <span>HD video export (1080p)</span>
              </li>
            </ul>
          </div>
          <div class="card-footer">
            <button
              v-if="currentPlan === 'premium'"
              class="btn btn-current"
              disabled
            >
              Current Plan
            </button>
            <button
              v-else
              class="btn btn-premium"
              @click="openPaymentModal('premium')"
              :disabled="processingPayment"
            >
              Upgrade
            </button>
          </div>
        </div>
      </div>

      <!-- FAQ Section -->
      <div class="faq-section">
        <h2>Frequently Asked Questions</h2>
        <div class="faq-grid">
          <div class="faq-item">
            <h4>Can I cancel anytime?</h4>
            <p>Yes, you can cancel your subscription at any time. Your plan will remain active until the end of the billing period.</p>
          </div>
          <div class="faq-item">
            <h4>What payment methods do you accept?</h4>
            <p>We accept PayPal and all major credit/debit cards through PayPal's secure payment system.</p>
          </div>
          <div class="faq-item">
            <h4>Can I change my plan later?</h4>
            <p>Absolutely! You can upgrade or downgrade your plan at any time from your account settings.</p>
          </div>
          <div class="faq-item">
            <h4>Is there a free trial?</h4>
            <p>Our Free plan lets you try all basic features. Upgrade when you're ready for more!</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <Teleport to="body">
      <div v-if="showPaymentModal" class="modal-overlay" @click.self="closePaymentModal">
        <div class="payment-modal">
          <div class="modal-header">
            <h3>Complete Your Purchase</h3>
            <button class="close-btn" @click="closePaymentModal">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="plan-summary">
              <div class="plan-info">
                <span class="plan-label">{{ getPlanName(selectedPlan) }} Plan</span>
                <span class="plan-price">${{ selectedPlan === 'basic' ? '9.90' : '19.90' }}/month</span>
              </div>
              <p class="plan-description">30 days of premium features</p>
            </div>

            <div class="payment-methods">
              <h4>Select Payment Method</h4>

              <!-- PayPal Button Container -->
              <div id="paypal-button-container" class="paypal-buttons"></div>

              <!-- Loading State -->
              <div v-if="loadingPaypal" class="loading-paypal">
                <div class="spinner"></div>
                <p>Loading payment options...</p>
              </div>

              <!-- Error State -->
              <div v-if="paymentError" class="payment-error">
                <p>{{ paymentError }}</p>
                <button class="btn btn-secondary" @click="retryPayment">Try Again</button>
              </div>
            </div>

            <div class="secure-badge">
              <svg viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
              </svg>
              <span>Secured by PayPal</span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api'
import api from '@/api/http'

const route = useRoute()
const userStore = useUserStore()

const currentPlan = ref('free')
const expiresAt = ref<string | null>(null)
const showPaymentModal = ref(false)
const selectedPlan = ref<'basic' | 'premium'>('basic')
const processingPayment = ref(false)
const loadingPaypal = ref(false)
const paymentError = ref('')
const paymentSuccess = ref(false)
const paymentCancelled = ref(false)

// PayPal 配置
const paypalClientId = ref('')
const paypalLoaded = ref(false)

const getPlanName = (plan: string) => {
  const names: Record<string, string> = {
    free: 'Free',
    basic: 'Basic',
    premium: 'Premium'
  }
  return names[plan] || plan
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const loadPaymentConfig = async () => {
  try {
    const res = await api.get('/payment/config')
    paypalClientId.value = res.data.data.paypal_client_id
  } catch (error) {
    console.error('Failed to load payment config:', error)
  }
}

const loadPayPalScript = () => {
  return new Promise<void>((resolve, reject) => {
    if (paypalLoaded.value) {
      resolve()
      return
    }

    // 检查是否已经加载
    if ((window as any).paypal) {
      paypalLoaded.value = true
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = `https://www.paypal.com/sdk/js?client-id=${paypalClientId.value}&currency=USD`
    script.onload = () => {
      paypalLoaded.value = true
      resolve()
    }
    script.onerror = () => {
      reject(new Error('Failed to load PayPal SDK'))
    }
    document.head.appendChild(script)
  })
}

const renderPayPalButtons = async () => {
  loadingPaypal.value = true
  paymentError.value = ''

  try {
    await loadPayPalScript()

    // 清空容器
    const container = document.getElementById('paypal-button-container')
    if (container) {
      container.innerHTML = ''
    }

    // 渲染按钮
    ;(window as any).paypal.Buttons({
      style: {
        layout: 'vertical',
        color: 'gold',
        shape: 'rect',
        label: 'paypal'
      },
      createOrder: async () => {
        try {
          const res = await api.post('/payment/orders', {
            plan: selectedPlan.value
          })
          return res.data.data.order_id
        } catch (error: any) {
          console.error('Failed to create order:', error)
          paymentError.value = error.response?.data?.detail || 'Failed to create order'
          throw error
        }
      },
      onApprove: async (data: any) => {
        processingPayment.value = true
        try {
          const res = await api.post(`/payment/orders/${data.orderID}/capture`)
          if (res.data.data.status === 'success') {
            currentPlan.value = res.data.data.plan
            expiresAt.value = res.data.data.expires_at
            paymentSuccess.value = true
            closePaymentModal()
            // 刷新用户信息
            await userStore.fetchProfile()
          }
        } catch (error: any) {
          console.error('Failed to capture payment:', error)
          paymentError.value = error.response?.data?.detail || 'Payment failed'
        } finally {
          processingPayment.value = false
        }
      },
      onCancel: () => {
        console.log('Payment cancelled by user')
      },
      onError: (err: any) => {
        console.error('PayPal error:', err)
        paymentError.value = 'An error occurred with PayPal. Please try again.'
      }
    }).render('#paypal-button-container')

  } catch (error) {
    console.error('Failed to render PayPal buttons:', error)
    paymentError.value = 'Failed to load payment options. Please refresh and try again.'
  } finally {
    loadingPaypal.value = false
  }
}

const openPaymentModal = async (plan: 'basic' | 'premium') => {
  selectedPlan.value = plan
  showPaymentModal.value = true
  paymentError.value = ''

  // 等待 DOM 更新后渲染 PayPal 按钮
  setTimeout(() => {
    renderPayPalButtons()
  }, 100)
}

const closePaymentModal = () => {
  showPaymentModal.value = false
  paymentError.value = ''
}

const retryPayment = () => {
  paymentError.value = ''
  renderPayPalButtons()
}

onMounted(async () => {
  // 检查 URL 参数
  if (route.query.success === 'true') {
    paymentSuccess.value = true
    // 移除 URL 参数
    window.history.replaceState({}, '', '/subscription')
  }
  if (route.query.cancelled === 'true') {
    paymentCancelled.value = true
    window.history.replaceState({}, '', '/subscription')
  }

  // 加载支付配置
  await loadPaymentConfig()

  // 加载用户订阅信息
  try {
    const res = await userApi.getProfile()
    if (res.data?.subscription) {
      currentPlan.value = res.data.subscription.plan || 'free'
      expiresAt.value = res.data.subscription.expires_at
    }
  } catch (error) {
    console.error('Failed to load subscription info:', error)
  }
})
</script>

<style scoped>
.subscription-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 100%);
  padding: 40px 20px 80px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
}

.subtitle {
  font-size: 18px;
  color: #999;
}

/* Alerts */
.alert {
  padding: 16px 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 14px;
}

.alert-success {
  background: rgba(52, 199, 89, 0.15);
  border: 1px solid rgba(52, 199, 89, 0.3);
  color: #34c759;
}

.alert-warning {
  background: rgba(255, 159, 10, 0.15);
  border: 1px solid rgba(255, 159, 10, 0.3);
  color: #ff9f0a;
}

/* Current Plan Banner */
.current-plan-banner {
  background: rgba(45, 107, 107, 0.2);
  border: 1px solid rgba(45, 107, 107, 0.4);
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 40px;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.banner-content .badge {
  background: #2D6B6B;
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.banner-content .plan-name {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.banner-content .expires {
  color: #999;
  font-size: 14px;
  margin-left: auto;
}

/* Pricing Grid */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 60px;
}

@media (max-width: 900px) {
  .pricing-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }
}

/* Pricing Card */
.pricing-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 32px 24px;
  position: relative;
  transition: all 0.3s ease;
}

.pricing-card:hover {
  border-color: #444;
  transform: translateY(-4px);
}

.pricing-card.active {
  border-color: #2D6B6B;
  box-shadow: 0 0 20px rgba(45, 107, 107, 0.2);
}

.pricing-card.premium {
  border-color: #2D6B6B;
  background: linear-gradient(180deg, #1a2a2a 0%, #1a1a1a 100%);
}

.popular-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #2D6B6B 0%, #3D8B8B 100%);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

/* Card Header */
.card-header {
  text-align: center;
  padding-bottom: 24px;
  border-bottom: 1px solid #333;
  margin-bottom: 24px;
}

.card-header h3 {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.price .amount {
  font-size: 48px;
  font-weight: 700;
  color: #fff;
}

.price .period {
  font-size: 16px;
  color: #999;
}

/* Card Body */
.card-body {
  min-height: 280px;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  color: #fff;
  font-size: 14px;
}

.features li.disabled {
  color: #666;
}

.check-icon {
  width: 20px;
  height: 20px;
  fill: #2D6B6B;
  flex-shrink: 0;
}

.x-icon {
  width: 20px;
  height: 20px;
  fill: #666;
  flex-shrink: 0;
}

/* Card Footer */
.card-footer {
  padding-top: 24px;
}

.btn {
  width: 100%;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-primary {
  background: #2D6B6B;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #3D7B7B;
}

.btn-secondary {
  background: transparent;
  border: 1px solid #444;
  color: #fff;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #666;
  background: rgba(255, 255, 255, 0.05);
}

.btn-premium {
  background: linear-gradient(135deg, #2D6B6B 0%, #3D8B8B 100%);
  color: #fff;
}

.btn-premium:hover:not(:disabled) {
  background: linear-gradient(135deg, #3D7B7B 0%, #4D9B9B 100%);
}

.btn-current {
  background: rgba(45, 107, 107, 0.2);
  color: #2D6B6B;
  cursor: default;
}

/* FAQ Section */
.faq-section {
  margin-top: 60px;
}

.faq-section h2 {
  text-align: center;
  font-size: 28px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 32px;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

@media (max-width: 768px) {
  .faq-grid {
    grid-template-columns: 1fr;
  }
}

.faq-item {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
}

.faq-item h4 {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
}

.faq-item p {
  font-size: 14px;
  color: #999;
  line-height: 1.6;
}

/* Payment Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.payment-modal {
  background: #1a1a1a;
  border-radius: 20px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #333;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 24px;
}

.plan-summary {
  background: #252525;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.plan-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.plan-label {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.plan-price {
  font-size: 24px;
  font-weight: 700;
  color: #2D6B6B;
}

.plan-description {
  font-size: 14px;
  color: #999;
}

.payment-methods h4 {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
}

.paypal-buttons {
  min-height: 150px;
}

.loading-paypal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #999;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top-color: #2D6B6B;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.payment-error {
  text-align: center;
  padding: 20px;
  background: rgba(255, 59, 48, 0.1);
  border-radius: 12px;
  margin-top: 16px;
}

.payment-error p {
  color: #ff3b30;
  margin-bottom: 12px;
}

.secure-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #333;
  color: #666;
  font-size: 12px;
}
</style>
