<!-- src/components/TagChip.vue -->
<template>
  <span
    class="tag-chip"
    :style="{ backgroundColor: bgColor, color: textColor }"
    @click="handleClick"
  >
    #{{ name }}
  </span>
</template>

<script setup>

const props = defineProps({
  name: {
    type: String,
    required: true
  }
})

// 简单颜色生成（基于标签名哈希）
const hashCode = (str) => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // 转为32位整数
  }
  return Math.abs(hash)
}

const bgColor = `hsl(${hashCode(props.name) % 360}, 70%, 90%)`
const textColor = `hsl(${hashCode(props.name) % 360}, 70%, 30%)`

const emit = defineEmits(['click'])

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.tag-chip {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.tag-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
</style>