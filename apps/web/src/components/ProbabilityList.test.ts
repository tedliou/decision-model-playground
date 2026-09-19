import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProbabilityList from './ProbabilityList.vue'

describe('probability display', () => {
  it('shows none and zero-probability articles without changing model values', () => {
    const wrapper = mount(ProbabilityList, {
      props: {
        selectedId: 'none',
        options: [
          {
            id: 'none',
            title: '沒有可推薦的',
            url: null,
            summary: '',
            category: '',
            probability: 0.9999,
            is_none: true,
          },
          {
            id: 'a01',
            title: '文章',
            url: 'https://vervecode.dev/',
            summary: '',
            category: '',
            probability: 0.0001,
            is_none: false,
          },
          {
            id: 'a02',
            title: '其他文章',
            url: 'https://vervecode.dev/',
            summary: '',
            category: '',
            probability: 0,
            is_none: false,
          },
        ],
      },
    })
    expect(wrapper.findAll('[role="progressbar"]')).toHaveLength(3)
    expect(wrapper.text()).toContain('99.99%')
    expect(wrapper.text()).toContain('0.01%')
    expect(wrapper.text()).toContain('0.00%')
    expect(wrapper.find('.selected').text()).toContain('沒有可推薦的')
    expect(wrapper.find('.selected a').exists()).toBe(false)
  })
})
