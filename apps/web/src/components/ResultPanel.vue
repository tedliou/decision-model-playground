<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ArrowUpRight, Check, Clock3, CircleSlash, SlidersHorizontal } from '@lucide/vue'
import type { Option, Recommendation } from '../api/client'
import ProbabilityList from './ProbabilityList.vue'

defineProps<{ result: Recommendation; winner: Option; roundTripMs: number }>()
const duration = (ms: number) =>
  ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${ms.toFixed(0)} ms`

const panel = ref<HTMLElement>()
onMounted(() => {
  if (window.matchMedia('(max-width: 760px)').matches) {
    panel.value?.scrollIntoView({ block: 'start' })
  }
})
</script>

<template>
  <section ref="panel" class="results" aria-label="推薦結果">
    <div class="section-heading">
      <h2>
        本次結果 <span class="model-tag">{{ result.provider === 'laya' ? 'Laya' : 'Jev' }}</span>
      </h2>
      <span class="finished"><Check :size="14" />已完成</span>
    </div>
    <p class="result-query">「{{ result.question }}」</p>
    <div class="winner-card" :class="{ 'no-winner': winner.is_none }" aria-live="polite">
      <div class="eyebrow">
        <CircleSlash v-if="winner.is_none" :size="15" /><span v-else class="winner-dot"></span>
        {{ winner.is_none ? '這次沒有合適的文章' : '模型最推薦' }}
      </div>
      <h3>{{ winner.title }}</h3>
      <p>{{ winner.summary }}</p>
      <div class="winner-footer">
        <span
          ><strong>{{ (winner.probability * 100).toFixed(2) }}%</strong> 選項機率</span
        >
        <a v-if="winner.url" :href="winner.url" target="_blank" rel="noopener noreferrer"
          >閱讀文章 <ArrowUpRight :size="17"
        /></a>
      </div>
    </div>
    <div class="timing-strip">
      <div>
        <span
          ><Clock3 :size="13" />{{ result.provider === 'jev' ? '模型 API 往返' : '模型推論' }}</span
        ><strong>{{ duration(result.timing.inference_ms) }}</strong>
      </div>
      <div>
        <span>模型載入</span
        ><strong
          >{{ duration(result.timing.model_load_ms)
          }}<small v-if="result.timing.model_load_ms === 0"> 已就緒</small></strong
        >
      </div>
      <div>
        <span>整次請求</span><strong>{{ duration(roundTripMs) }}</strong>
      </div>
    </div>
    <div class="distribution-heading">
      <h3>所有選項的機率</h3>
      <span>{{ result.options.length }} 個選項 · 由高到低</span>
    </div>
    <p class="distribution-note">
      機率表示這次選擇中的相對偏好，不代表文章一定能解決問題。包含「沒有可推薦的」。
    </p>
    <ProbabilityList :options="result.options" :selected-id="result.recommended_id" />
    <details class="experiment-details">
      <summary><SlidersHorizontal :size="15" />實驗資訊</summary>
      <dl>
        <dt>模型</dt>
        <dd>{{ result.model }}</dd>
        <dt>執行位置</dt>
        <dd>{{ result.device }}</dd>
        <dt>輸入 tokens</dt>
        <dd>{{ result.input_tokens ?? '未提供' }}</dd>
        <dt>後端總耗時</dt>
        <dd>{{ duration(result.timing.server_total_ms) }}</dd>
        <dt>文章快照</dt>
        <dd>{{ result.catalog_version }}</dd>
        <dt>題目版本</dt>
        <dd>{{ result.prompt_version }}</dd>
        <dt v-if="result.model_revision">模型版本</dt>
        <dd v-if="result.model_revision">{{ result.model_revision }}</dd>
      </dl>
      <p>
        直接顯示模型回傳的 Choice 機率，沒有重新配分；四捨五入後總和可能略有誤差。Jev
        計時包含網路往返，Laya 計時包含輸入處理與 GPU 同步。
      </p>
    </details>
  </section>
</template>
