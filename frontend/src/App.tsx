import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { chrome } from './i18n'
import type { Language } from './i18n'

type Severity = 'BLOCKER' | 'WARNING' | 'INFO'
type Actor = 'CITIZEN' | 'EMPLOYER' | 'BANK'
type Copy = { [Key in keyof typeof chrome.en]: string }

type Issue = {
  rule_id: string
  severity: Severity
  actor: Actor
  field_read: string
  observed_value: unknown
  why: string
  fix: string
  eta_days: number
}

type PreflightResponse = {
  profile: Record<string, unknown>
  language: string
  scrubbed_text: string
  stripped_types: string[]
  verdict: string
  ordered_issues: Issue[]
  verified_sentences: string[]
  needs_human_review: string[]
}

type DraftResponse = { message: string; rule_whys: string[] }
type SubmitResponse = { submitted: boolean; blocking_rule_ids: string[]; needs_human_review: string[] }

const demos = [
  ['999000000001', 'A · Clean profile — the happy path'],
  ['999000000002', 'B · KYC approval and an exit date are missing'],
  ['999000000003', 'C · Name mismatch and unverified bank IFSC'],
  ['999000000004', 'D · Tax warning and wrong claim form'],
  ['999000000005', 'E · UAN activation and member-ID transfer needed'],
] as const

const booleanFields = new Set(['uan_activated', 'kyc_approved', 'bank_ifsc_verified', 'account_is_joint', 'aadhaar_seeded'])
const numberFields = new Set(['service_months', 'eps_contribution_months', 'claim_amount'])
const dateFields = new Set(['dob_epfo', 'dob_aadhaar', 'date_of_exit'])

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}

function withoutRulePrefix(text: string): string {
  return text.replace(/^R\d{2}:\s*/, '')
}

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'not recorded'
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  if (typeof value === 'object') return JSON.stringify(value).replaceAll('"', '')
  return String(value)
}

function PrototypeBanner({ children }: { children: string }) {
  return <div className="border-b border-amber-200 bg-amber-50 px-4 py-3 text-center text-sm leading-5 text-amber-950">{children}</div>
}

function Skeleton({ cards = 3 }: { cards?: number }) {
  return <main className="mx-auto w-full max-w-3xl space-y-4 px-4 py-8" aria-busy="true">
    <div className="h-8 w-44 animate-pulse rounded bg-slate-200" />
    <div className="h-28 animate-pulse rounded-3xl bg-slate-200" />
    {Array.from({ length: cards }, (_, index) => <div key={index} className="space-y-3 rounded-3xl border border-slate-100 bg-white p-5"><div className="h-5 w-20 animate-pulse rounded bg-slate-200" /><div className="h-5 w-full animate-pulse rounded bg-slate-100" /><div className="h-5 w-4/5 animate-pulse rounded bg-slate-100" /><div className="h-12 animate-pulse rounded-xl bg-slate-100" /></div>)}
  </main>
}

function RuleTag({ issue }: { issue: Issue }) {
  const colors = issue.severity === 'WARNING' ? 'bg-amber-100 text-amber-900' : 'bg-rose-100 text-rose-900'
  return <span className={`rounded-full px-2.5 py-1 text-xs font-bold tracking-wide ${colors}`}>{issue.rule_id}</span>
}

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [uan, setUan] = useState('')
  const [intakeText, setIntakeText] = useState('')
  const [result, setResult] = useState<PreflightResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [draftLoading, setDraftLoading] = useState(false)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [draft, setDraft] = useState<DraftResponse | null>(null)
  const [outcome, setOutcome] = useState<SubmitResponse | null>(null)
  const [reviewed, setReviewed] = useState(false)
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const t = chrome[language] as Copy

  const explanations = useMemo(() => new Map((result?.verified_sentences ?? []).map((sentence) => [sentence.match(/^R\d{2}/)?.[0] ?? '', sentence])), [result])
  const blockers = result?.ordered_issues.filter((issue) => issue.severity === 'BLOCKER').length ?? 0
  const warnings = result?.ordered_issues.filter((issue) => issue.severity === 'WARNING').length ?? 0

  async function checkClaim(event: FormEvent) {
    event.preventDefault()
    if (!uan) return setError(t.chooseRecord)
    setError(null); setDraft(null); setOutcome(null); setLoading(true)
    try {
      setResult(await postJson<PreflightResponse>('/preflight', { uan, intake_text: intakeText, language }))
    } catch {
      setError(t.error)
    } finally {
      setLoading(false)
    }
  }

  async function saveOverride(overrides: Record<string, unknown>) {
    if (!result) return
    setError(null); setEditingRuleId(null); setLoading(true)
    try {
      setResult(await postJson<PreflightResponse>('/override', { state: result, overrides }))
      setReviewed(false); setDraft(null); setOutcome(null)
    } catch {
      setError(t.error)
    } finally {
      setLoading(false)
    }
  }

  async function makeDraft() {
    if (!result) return
    setError(null); setDraftLoading(true)
    try {
      setDraft(await postJson<DraftResponse>('/draft', { state: result, recipient: 'EMPLOYER' }))
    } catch {
      setError(t.error)
    } finally {
      setDraftLoading(false)
    }
  }

  async function submitMock() {
    if (!result || !reviewed) return
    setError(null); setSubmitLoading(true)
    try {
      setOutcome(await postJson<SubmitResponse>('/submit-mock', { state: result, review_confirmed: true }))
    } catch {
      setError(t.error)
    } finally {
      setSubmitLoading(false)
    }
  }

  function reset() {
    setResult(null); setOutcome(null); setDraft(null); setReviewed(false); setEditingRuleId(null); setError(null)
  }

  if (loading) return <div className="min-h-screen bg-slate-50 font-sans text-slate-950"><PrototypeBanner>{t.prototype}</PrototypeBanner><Skeleton /></div>

  if (outcome && result) return <div className="min-h-screen bg-slate-50 font-sans text-slate-950"><PrototypeBanner>{t.prototype}</PrototypeBanner><main className="mx-auto flex min-h-[calc(100vh-52px)] w-full max-w-xl items-center px-4 py-8"><section className="w-full rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-bold uppercase tracking-widest text-slate-500">{t.outcome}</p><h1 className="mt-3 text-3xl font-bold tracking-tight">{outcome.submitted ? t.accepted : t.blocked}</h1>{!outcome.submitted && <p className="mt-5 rounded-2xl bg-rose-50 p-4 font-semibold text-rose-950">{outcome.blocking_rule_ids.join(', ')}</p>}<button type="button" onClick={reset} className="mt-6 min-h-12 w-full rounded-xl bg-slate-950 px-4 py-3 text-base font-bold text-white">{t.startAgain}</button></section></main></div>

  if (!result) return <div className="min-h-screen bg-slate-50 font-sans text-slate-950"><PrototypeBanner>{t.prototype}</PrototypeBanner><main className="mx-auto w-full max-w-3xl px-4 py-8 sm:py-12"><section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-bold uppercase tracking-widest text-teal-700">{t.eyebrow}</p><h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">{t.title}</h1></div><select aria-label="Language" value={language} onChange={(event) => setLanguage(event.target.value as Language)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-base"><option value="en">English</option><option value="hi">हिंदी</option></select></div><p className="mt-4 text-base leading-7 text-slate-600">{t.intro}</p><form className="mt-7 space-y-6" onSubmit={checkClaim}><fieldset><legend className="text-base font-bold">{t.chooseProfile}</legend><div className="mt-3 grid gap-3">{demos.map(([demoUan, label]) => <label key={demoUan} className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-2xl border p-3 text-left ${uan === demoUan ? 'border-teal-700 bg-teal-50 ring-1 ring-teal-700' : 'border-slate-200'}`}><input type="radio" name="uan" checked={uan === demoUan} onChange={() => setUan(demoUan)} className="h-5 w-5 accent-teal-700" /><span><span className="block font-mono text-sm font-bold">{demoUan}</span><span className="block text-sm text-slate-600">{label}</span></span></label>)}</div></fieldset><label className="block text-base font-bold">{t.situation}<textarea value={intakeText} onChange={(event) => setIntakeText(event.target.value)} placeholder={t.situationHint} className="mt-3 min-h-32 w-full rounded-2xl border border-slate-300 p-4 text-base font-normal leading-6 outline-none ring-teal-700 placeholder:text-slate-400 focus:ring-2" /></label>{error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-base text-rose-800">{error}</p>}<button type="submit" className="min-h-12 w-full rounded-xl bg-teal-700 px-4 py-3 text-base font-bold text-white">{t.checkClaim}</button></form></section></main></div>

  return <div className="min-h-screen bg-slate-50 font-sans text-slate-950"><PrototypeBanner>{t.prototype}</PrototypeBanner><main className="mx-auto w-full max-w-3xl px-4 py-6 sm:py-10"><button type="button" onClick={reset} className="min-h-11 text-base font-semibold text-teal-800 underline underline-offset-4">← {t.back}</button>{error && <p role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-base text-rose-800">{error}</p>}{result.stripped_types.length > 0 && <aside className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-base leading-6 text-amber-950"><strong>{t.stripped} {result.stripped_types.join(', ')}</strong> {t.strippedWhy}</aside>}<section className="mt-5 rounded-3xl bg-slate-950 p-6 text-white shadow-sm sm:p-8"><p className="text-sm font-bold uppercase tracking-[0.2em] text-teal-300">{t.eyebrow}</p><h1 className="mt-3 text-4xl font-black tracking-tight">{result.verdict}</h1><p className="mt-4 text-lg text-slate-200"><strong>{blockers}</strong> {t.blockers} · <strong>{warnings}</strong> {t.warnings}</p></section><section className="mt-8"><div className="flex items-center justify-between"><h2 className="text-2xl font-bold tracking-tight">{t.issues}</h2><span className="rounded-full bg-slate-200 px-3 py-1 text-sm font-bold text-slate-700">{result.ordered_issues.length}</span></div>{result.ordered_issues.length === 0 ? <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-base text-emerald-950">{t.noIssues}</div> : <div className="mt-4 space-y-4">{result.ordered_issues.map((issue) => <IssueCard key={issue.rule_id} issue={issue} explanation={explanations.get(issue.rule_id) ?? issue.why} t={t} editing={editingRuleId === issue.rule_id} onEdit={() => setEditingRuleId(issue.rule_id)} onCancel={() => setEditingRuleId(null)} onSave={saveOverride} />)}</div>}</section><section className="mt-8 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><button type="button" onClick={makeDraft} disabled={draftLoading} className="min-h-12 w-full rounded-xl border border-teal-700 px-4 py-3 text-base font-bold text-teal-800 disabled:opacity-60">{draftLoading ? t.generatingDraft : t.generateDraft}</button>{draftLoading && <div className="mt-4 h-24 animate-pulse rounded-2xl bg-slate-100" />}{draft && !draftLoading && <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-base leading-7"><p className="font-bold">{t.draft}</p><p className="mt-2 whitespace-pre-wrap">{draft.message || draft.rule_whys.map(withoutRulePrefix).join('\n')}</p></div>}</section><section className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><label className="flex min-h-11 cursor-pointer items-start gap-3 text-base leading-6"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} className="mt-1 h-5 w-5 shrink-0 accent-teal-700" /><span>{t.review}</span></label>{submitLoading ? <div className="mt-5 h-12 animate-pulse rounded-xl bg-slate-100" /> : <button type="button" onClick={submitMock} disabled={!reviewed} className="mt-5 min-h-12 w-full rounded-xl bg-slate-950 px-4 py-3 text-base font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-600">{reviewed ? t.submit : t.submitDisabled}</button>}</section></main></div>
}

function IssueCard({ issue, explanation, t, editing, onEdit, onCancel, onSave }: { issue: Issue; explanation: string; t: Copy; editing: boolean; onEdit: () => void; onCancel: () => void; onSave: (overrides: Record<string, unknown>) => void }) {
  const fields = issue.field_read.split(',').map((field) => field.trim())
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(fields.map((field) => [field, fieldValue(issue.observed_value, field, fields.length)])))
  function submit(event: FormEvent) { event.preventDefault(); onSave(Object.fromEntries(fields.map((field) => [field, parsedValue(field, values[field] ?? '')]))) }
  return <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="flex items-start justify-between gap-4"><RuleTag issue={issue} /><span className="text-xs font-bold tracking-wide text-slate-500">{issue.severity}</span></div><p className="mt-4 text-lg font-semibold leading-7">{withoutRulePrefix(explanation)}</p><p className="mt-3 text-base leading-6 text-slate-700">{withoutRulePrefix(issue.fix)}</p><p className="mt-5 rounded-2xl bg-slate-50 p-4 text-base leading-6"><strong>{t.readFound} {issue.field_read}</strong> {t.andFound} <span className="font-mono text-sm">{valueText(issue.observed_value)}</span>.</p><dl className="mt-5 grid grid-cols-2 gap-3 text-base"><div><dt className="text-sm font-semibold text-slate-500">{t.whoFixes}</dt><dd className="mt-1 font-bold">{issue.actor}</dd></div><div><dt className="text-sm font-semibold text-slate-500">{t.eta}</dt><dd className="mt-1 font-bold">{issue.eta_days === 0 ? t.today : `${issue.eta_days} ${t.days}`}</dd></div></dl>{editing ? <form onSubmit={submit} className="mt-5 space-y-3 rounded-2xl border border-teal-200 bg-teal-50 p-4">{fields.map((field) => <OverrideInput key={field} field={field} value={values[field] ?? ''} onChange={(value) => setValues((current) => ({ ...current, [field]: value }))} />)}<div className="flex gap-3"><button type="submit" className="min-h-11 flex-1 rounded-xl bg-teal-700 px-3 py-2 text-base font-bold text-white">{t.saveOverride}</button><button type="button" onClick={onCancel} className="min-h-11 rounded-xl border border-slate-300 px-4 py-2 text-base font-semibold">{t.cancel}</button></div></form> : <button type="button" onClick={onEdit} className="mt-5 min-h-11 w-full rounded-xl border border-slate-300 px-4 py-2 text-base font-bold">{t.wrong}</button>}</article>
}

function OverrideInput({ field, value, onChange }: { field: string; value: string; onChange: (value: string) => void }) {
  if (booleanFields.has(field)) return <label className="flex min-h-11 items-center gap-3 text-base font-semibold"><input type="checkbox" checked={value === 'true'} onChange={(event) => onChange(String(event.target.checked))} className="h-5 w-5 accent-teal-700" />{field}</label>
  return <label className="block text-sm font-bold text-slate-800">{field}<input type={dateFields.has(field) ? 'date' : numberFields.has(field) ? 'number' : 'text'} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-base font-normal" /></label>
}

function fieldValue(observed: unknown, field: string, count: number): string {
  if (typeof observed === 'object' && observed !== null && !Array.isArray(observed) && count > 1) return String((observed as Record<string, unknown>)[field] ?? '')
  if (Array.isArray(observed)) return observed.join(', ')
  return observed === null || observed === undefined ? '' : String(observed)
}

function parsedValue(field: string, value: string): unknown {
  if (booleanFields.has(field)) return value === 'true'
  if (field === 'service_months' || field === 'eps_contribution_months') return Number(value)
  if (field === 'claim_amount') return value
  if (field === 'member_ids' || field === 'untransferred_member_ids') return value.split(',').map((item) => item.trim()).filter(Boolean)
  return value || null
}

export default App
