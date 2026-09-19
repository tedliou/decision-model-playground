import { computed, onUnmounted, ref } from 'vue'
import { recommend, type ProviderId, type Recommendation } from '../api/client'

export function useRecommendation() {
  const result = ref<Recommendation | null>(null)
  const pending = ref(false)
  const error = ref('')
  const elapsedMs = ref(0)
  const roundTripMs = ref(0)
  let timer: ReturnType<typeof setInterval> | undefined
  const winner = computed(() =>
    result.value?.options.find((option) => option.id === result.value?.recommended_id),
  )

  async function submit(question: string, provider: ProviderId) {
    if (pending.value || !question.trim()) return
    pending.value = true
    error.value = ''
    result.value = null
    elapsedMs.value = 0
    const started = performance.now()
    timer = setInterval(() => {
      elapsedMs.value = performance.now() - started
    }, 100)
    try {
      result.value = await recommend(question.trim(), provider)
      roundTripMs.value = performance.now() - started
    } catch (cause) {
      error.value =
        cause instanceof DOMException && cause.name === 'TimeoutError'
          ? '等待超過 3 分鐘，請查看後端狀態後再試。'
          : cause instanceof Error
            ? cause.message
            : '無法連線，請確認後端已啟動。'
    } finally {
      clearInterval(timer)
      pending.value = false
    }
  }

  onUnmounted(() => clearInterval(timer))
  return { result, pending, error, elapsedMs, roundTripMs, winner, submit }
}
