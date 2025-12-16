// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

// Views
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import HomeView from '@/views/HomeView.vue'
import SearchByTagsView from '@/views/SearchByTagsView.vue'

// 新增：必须的页面（请确保这些文件存在）
import PostCreateView from '@/views/PostCreateView.vue'     // 发帖
import PostDetailView from '@/views/PostDetailView.vue'     // 帖子详情
import ProfileView from '@/views/ProfileView.vue'           // 个人主页
import MyPostsView from '@/views/MyPostsView.vue'           // 我的帖子

// 可选：通用搜索页（支持关键词）
import SearchView from '@/views/SearchView.vue'             // /search?q=...

const routes = [
  { path: '/login', component: LoginView },
  { path: '/register', component: RegisterView },

  // 主页面（需登录）
  { path: '/', component: HomeView, meta: { requiresAuth: true } },

  // 帖子相关
  { path: '/post/create', component: PostCreateView, meta: { requiresAuth: true } },
  { path: '/post/:id', component: PostDetailView, meta: { requiresAuth: true } },

  // 用户相关
  { path: '/profile', component: ProfileView, meta: { requiresAuth: true } },
  { path: '/my-posts', component: MyPostsView, meta: { requiresAuth: true } },

  // 搜索
  { path: '/search/tags', component: SearchByTagsView, meta: { requiresAuth: true } },
  { path: '/search', component: SearchView, meta: { requiresAuth: true } }, // 支持 ?q=xxx
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth) {
    if (!token) {
      console.log('无 token，跳转登录')
      return next('/login')
    }

    try {
      const { getCurrentUser } = await import('@/api/auth')
      await getCurrentUser()
      next()
    } catch (err) {
      console.error('Token 无效或过期:', err)
      localStorage.removeItem('token')
      next('/login')
    }
  } else {
    // 已登录用户访问登录/注册页时，重定向到首页
    if (token && (to.path === '/login' || to.path === '/register')) {
      next('/')
    } else {
      next()
    }
  }
})

export default router