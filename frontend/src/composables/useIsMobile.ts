import { onMounted, onUnmounted, ref } from 'vue'

export const useIsMobile = (breakpoint = 900) => {
  // 统一暴露“是否移动端”响应式状态，供表格列宽/操作区切换使用。
  const isMobile = ref(false)
  let mediaQuery: MediaQueryList | null = null

  const handleChange = (event: MediaQueryListEvent) => {
    // 视口跨越断点时同步更新状态。
    isMobile.value = event.matches
  }

  onMounted(() => {
    // 首次进入页面立即计算，避免首帧布局抖动。
    mediaQuery = window.matchMedia(`(max-width: ${breakpoint}px)`)
    isMobile.value = mediaQuery.matches
    mediaQuery.addEventListener('change', handleChange)
  })

  onUnmounted(() => {
    // 组件卸载时移除监听，避免内存泄漏。
    if (mediaQuery) {
      mediaQuery.removeEventListener('change', handleChange)
    }
  })

  return { isMobile }
}
