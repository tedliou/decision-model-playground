import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

const client = createClient<paths>({ baseUrl: '' })

export type Metadata = components['schemas']['Metadata']
export type Recommendation = components['schemas']['RecommendationResponse']
export type Provider = components['schemas']['ProviderInfo']
export type Option = components['schemas']['OptionResult']
export type ProviderId = Provider['id']

export async function getMetadata(): Promise<Metadata> {
  const { data, error } = await client.GET('/api/v1/metadata', {
    signal: AbortSignal.timeout(10_000),
  })
  if (error || !data) throw new Error('無法取得文章與模型資訊，請確認後端已啟動。')
  return data
}

export async function recommend(question: string, provider: ProviderId): Promise<Recommendation> {
  const { data, error } = await client.POST('/api/v1/recommendations', {
    body: { question, provider },
    signal: AbortSignal.timeout(180_000),
  })
  if (error) throw new Error(error.error.message)
  if (!data) throw new Error('伺服器未回傳推薦結果。')
  return data
}
