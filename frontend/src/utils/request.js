// src/utils/request.js
import axios from 'axios'

const request = axios.create({
  // 不要加 /api！因为后端已经处理了
  baseURL: '/', // 或者留空
  timeout: 10000
})

export default request