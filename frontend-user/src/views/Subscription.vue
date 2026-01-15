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
              @click="selectPlan('free')"
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
              @click="selectPlan('basic')"
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
              @click="selectPlan('premium')"
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
            <p>We accept all major credit cards, PayPal, and Apple Pay.</p>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const currentPlan = ref('free')
const expiresAt = ref<string | null>(null)

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

const selectPlan = (plan: string) => {
  // TODO: Implement payment flow
  // For now, just show an alert
  if (plan === 'free') {
    alert('Downgrade functionality coming soon!')
  } else {
    alert(`Upgrade to ${getPlanName(plan)} - Payment integration coming soon!`)
  }
}

onMounted(async () => {
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

.btn-primary {
  background: #2D6B6B;
  color: #fff;
}

.btn-primary:hover {
  background: #3D7B7B;
}

.btn-secondary {
  background: transparent;
  border: 1px solid #444;
  color: #fff;
}

.btn-secondary:hover {
  border-color: #666;
  background: rgba(255, 255, 255, 0.05);
}

.btn-premium {
  background: linear-gradient(135deg, #2D6B6B 0%, #3D8B8B 100%);
  color: #fff;
}

.btn-premium:hover {
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
</style>
