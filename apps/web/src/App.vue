<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  ChevronDown,
  FlaskConical,
  LoaderCircle,
  Sparkles,
  TriangleAlert,
} from '@lucide/vue'
import { getMetadata, type Metadata, type ProviderId } from './api/client'
import ResultPanel from './components/ResultPanel.vue'
import { useRecommendation } from './composables/useRecommendation'

const metadata = ref<Metadata | null>(null)
const metadataError = ref('')
const question = ref('')
const provider = ref<ProviderId>('laya')
const { result, winner, pending, error, elapsedMs, roundTripMs, submit } = useRecommendation()
const activeProvider = computed(() =>
  metadata.value?.providers.find((p) => p.id === provider.value),
)
const examples = [
  '我想讓 AI 幫我操作 TouchDesigner',
  'Astro 網站每次部署都要很久，怎麼加速？',
  '如何讓 Unity 使用 VS Code 寫 C#？',
  '怎麼煮出好吃的義大利麵？',
]

async function loadMetadata() {
  metadataError.value = ''
  try {
    metadata.value = await getMetadata()
  } catch {
    metadataError.value = '無法連線到後端，請確認服務已啟動。'
  }
}

async function run() {
  if (!activeProvider.value?.available) return
  await submit(question.value, provider.value)
  await loadMetadata()
}

watch(provider, () => {
  result.value = null
  error.value = ''
})
onMounted(loadMetadata)
</script>

<template>
  <header class="site-header">
    <a class="brand" href="/" aria-label="VerveCode 模型實驗室首頁"
      ><span class="brand-mark">v<span>c</span></span
      ><strong>VerveCode</strong><span class="header-divider"></span
      ><span class="brand-subtitle">模型實驗室</span></a
    >
    <a class="site-link" href="https://vervecode.dev/" target="_blank" rel="noopener noreferrer"
      >前往網站<ArrowUpRight :size="15"
    /></a>
  </header>
  <main>
    <section class="intro">
      <div class="eyebrow">
        <FlaskConical :size="15" />EXPERIMENT 01 <span>／</span> ARTICLE MATCHING
      </div>
      <h1>下一篇，<span>讀什麼？</span></h1>
      <p>
        帶著一個問題，看看模型會如何選擇。<br class="mobile-break" />探索 VerveCode
        文章之間的可能答案。
      </p>
      <div class="intro-meta">
        <span class="status-dot"></span>本機實驗 <span class="meta-separator">·</span
        >{{ metadata?.catalog.articles.length ?? '—' }} 篇文章<span class="meta-separator">·</span
        >Laya / Jev
      </div>
    </section>

    <div v-if="metadataError" class="error-box" role="alert">
      <TriangleAlert :size="18" />{{ metadataError }}<button @click="loadMetadata">重新連線</button>
    </div>

    <div class="workspace">
      <aside class="question-panel">
        <form @submit.prevent="run">
          <div class="section-heading">
            <h2><span class="step-number">01</span>提出問題</h2>
            <span class="small-label">YOUR QUESTION</span>
          </div>
          <label class="input-label" for="question">你想了解什麼？</label>
          <textarea
            id="question"
            v-model="question"
            maxlength="500"
            :disabled="pending"
            placeholder="例如：我想讓 AI 幫我操作 TouchDesigner，要從哪裡開始？"
            required
          ></textarea>
          <div class="input-caption">
            <span>用自己的話描述就好</span><span>{{ question.length }} / 500</span>
          </div>
          <label class="input-label model-label" for="provider">選擇模型</label>
          <div class="select-wrap">
            <select id="provider" v-model="provider" :disabled="pending || !metadata">
              <option
                v-for="item in metadata?.providers ?? []"
                :key="item.id"
                :value="item.id"
                :disabled="!item.available"
              >
                {{ item.name }}{{ !item.available ? ' · 尚未設定' : '' }}
              </option>
              <option v-if="!metadata" value="laya">Laya Multilingual</option></select
            ><ChevronDown :size="16" />
          </div>
          <p class="model-hint">
            {{
              activeProvider?.reason ??
              (provider === 'laya'
                ? activeProvider?.loaded
                  ? '本機執行 · 多語模型 · 已載入'
                  : '本機執行 · 多語模型 · 首次送出需要載入'
                : 'TypeSafe API · 使用相同文章與選項')
            }}
          </p>
          <button
            class="submit-button"
            type="submit"
            :disabled="pending || !question.trim() || !activeProvider?.available"
          >
            <LoaderCircle v-if="pending" :size="18" class="spin" /><span>{{
              pending ? '正在尋找答案' : '尋找推薦文章'
            }}</span
            ><ArrowRight v-if="!pending" :size="18" />
          </button>
          <p v-if="error" class="error-box" role="alert"><TriangleAlert :size="17" />{{ error }}</p>
        </form>
        <div class="examples">
          <h3>還沒想到問題？試試這些</h3>
          <button
            v-for="example in examples"
            :key="example"
            :disabled="pending"
            @click="question = example"
          >
            {{ example }}<ArrowUpRight :size="14" />
          </button>
        </div>
        <div class="experiment-note">
          <Sparkles :size="17" />
          <p>這是一場模型實驗。<br />推薦可能不準確，觀察它如何選擇，也是實驗的一部分。</p>
        </div>
        <details class="experiment-details">
          <summary>模型看到的文章選項</summary>
          <p>用精簡英文主題代表每篇文章，讓所有選項完整放入模型。中文標題與摘要供結果閱讀使用。</p>
          <dl>
            <template v-for="article in metadata?.catalog.articles ?? []" :key="article.id">
              <dt>{{ article.id }}</dt>
              <dd :title="article.title">{{ article.decision_label }}</dd>
            </template>
            <dt>none</dt>
            <dd>No relevant article</dd>
          </dl>
        </details>
      </aside>

      <ResultPanel
        v-if="result && winner"
        :result="result"
        :winner="winner"
        :round-trip-ms="roundTripMs"
      />
      <section v-else class="empty-panel" :aria-busy="pending" aria-label="推薦結果">
        <div class="section-heading">
          <h2><span class="step-number">02</span>觀察模型的選擇</h2>
          <span class="small-label">THE RESULTS</span>
        </div>
        <div class="empty-content" aria-live="polite">
          <div class="empty-illustration" :class="{ thinking: pending }">
            <div class="illustration-card back"></div>
            <div class="illustration-card front">
              <BookOpen :size="34" :stroke-width="1.3" /><span></span><span></span>
            </div>
            <span class="illustration-spark">✳</span>
          </div>
          <template v-if="pending"
            ><h3>模型正在閱讀候選文章</h3>
            <p>第一次使用 Laya 會先載入模型，<br />完成後就會顯示每個選項的機率。</p>
            <div class="loading-timer">
              <LoaderCircle :size="15" class="spin" />{{ (elapsedMs / 1000).toFixed(1) }} 秒
            </div></template
          >
          <template v-else
            ><h3>一個問題，一次新的探索。</h3>
            <p>送出問題後，這裡會顯示最推薦的文章、<br />所有選項的機率，以及模型花費的時間。</p>
            <span class="empty-pill"
              >{{
                (metadata?.catalog.articles.length ?? 18) + 1
              }}
              個選項，包含「沒有可推薦的」</span
            ></template
          >
        </div>
        <div class="empty-footer">
          <span>01 提出問題</span><ArrowRight :size="14" /><span>02 模型判斷</span
          ><ArrowRight :size="14" /><span>03 比較機率</span>
        </div>
      </section>
    </div>

    <footer class="page-footer">
      <span>VerveCode <span class="footer-dot">/</span> Model Playground</span
      ><span
        >文章來自
        <a href="https://vervecode.dev/" target="_blank" rel="noopener noreferrer">vervecode.dev</a>
        · 以精簡描述進行推薦</span
      >
    </footer>
  </main>
</template>
