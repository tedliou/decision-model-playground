import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { useRecommendation } from './useRecommendation'
import { recommend } from '../api/client'

vi.mock('../api/client', () => ({ recommend: vi.fn() }))

describe('request lifecycle', () => {
  it('prevents duplicate submits and allows retry after an error', async () => {
    let reject!: (reason: Error) => void
    vi.mocked(recommend).mockImplementationOnce(
      () =>
        new Promise((_, rejectFn) => {
          reject = rejectFn
        }),
    )
    let state!: ReturnType<typeof useRecommendation>
    const wrapper = mount(
      defineComponent({
        setup() {
          state = useRecommendation()
          return () => null
        },
      }),
    )
    void state.submit('test', 'laya')
    await state.submit('duplicate', 'laya')
    expect(recommend).toHaveBeenCalledTimes(1)
    expect(state.pending.value).toBe(true)
    reject(new Error('模型忙碌'))
    await flushPromises()
    expect(state.pending.value).toBe(false)
    expect(state.error.value).toBe('模型忙碌')
    expect(state.result.value).toBeNull()
    wrapper.unmount()
  })
})
