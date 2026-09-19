<script setup lang="ts">
import { ArrowUpRight, Ban } from '@lucide/vue'
import type { Option } from '../api/client'

defineProps<{ options: Option[]; selectedId: string }>()
const percent = (value: number) => (value * 100).toFixed(2)
</script>

<template>
  <ol class="probability-list" aria-label="所有選項機率">
    <li
      v-for="(option, index) in options"
      :key="option.id"
      class="probability-row"
      :class="{ selected: option.id === selectedId, 'none-option': option.is_none }"
    >
      <span class="rank">{{ String(index + 1).padStart(2, '0') }}</span>
      <div class="option-content">
        <div class="option-heading">
          <a v-if="option.url" :href="option.url" target="_blank" rel="noopener noreferrer">
            {{ option.title }}<ArrowUpRight :size="13" aria-hidden="true" />
          </a>
          <span v-else class="none-title"
            ><Ban :size="14" aria-hidden="true" />{{ option.title }}</span
          >
          <strong class="probability-number"
            >{{ percent(option.probability) }}<small>%</small></strong
          >
        </div>
        <div
          class="probability-track"
          role="progressbar"
          :aria-label="option.title"
          :aria-valuenow="Number(percent(option.probability))"
          :aria-valuemin="0"
          :aria-valuemax="100"
        >
          <div class="probability-fill" :style="{ width: `${option.probability * 100}%` }"></div>
        </div>
      </div>
    </li>
  </ol>
</template>
