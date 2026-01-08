import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: 'Echobot - AI Story Platform' }
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('@/views/Discover.vue'),
    meta: { title: 'Discover Stories - Echobot' }
  },
  {
    path: '/story/:id',
    name: 'StoryPlayer',
    component: () => import('@/views/StoryPlayer.vue'),
    meta: { title: 'Story Player - Echobot' }
  },
  {
    path: '/studio',
    name: 'Studio',
    component: () => import('@/views/Studio.vue'),
    meta: { title: 'AI Studio - Echobot', requiresAuth: true }
  },
  {
    path: '/audiobook',
    name: 'Audiobook',
    component: () => import('@/views/Audiobook.vue'),
    meta: { title: 'Audiobook - Echobot', requiresAuth: true }
  },
  {
    path: '/profiles',
    name: 'Profiles',
    component: () => import('@/views/Profiles.vue'),
    meta: { title: 'My Profiles - Echobot', requiresAuth: true },
    children: [
      {
        path: 'voice',
        name: 'VoiceProfiles',
        component: () => import('@/views/profiles/VoiceProfiles.vue'),
      },
      {
        path: 'avatar',
        name: 'AvatarProfiles',
        component: () => import('@/views/profiles/AvatarProfiles.vue'),
      },
      {
        path: 'creations',
        name: 'MyCreations',
        component: () => import('@/views/profiles/MyCreations.vue'),
      }
    ]
  },
  {
    path: '/account',
    name: 'Account',
    component: () => import('@/views/Account.vue'),
    meta: { title: 'Account Settings - Echobot', requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: 'Sign In - Echobot', hideNavbar: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: 'Sign Up - Echobot', hideNavbar: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: 'Page Not Found - Echobot' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Route guard
router.beforeEach((to, from, next) => {
  // Set page title
  document.title = (to.meta.title as string) || 'Echobot'

  // Check if auth required
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }

  next()
})

export default router
