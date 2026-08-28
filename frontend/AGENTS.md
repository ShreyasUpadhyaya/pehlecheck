# frontend

Mobile first. Design target is a 360px screen on a slow connection.

## Rules

- Explanation renders ABOVE the recommendation on every card. Not below.
- No confidence scores, no percentages, no gauges. A verdict, not a number.
- Every issue card ends with a "This is wrong about me" button that opens an
  override and recomputes.
- The submit button stays visibly disabled and labelled until the citizen
  ticks the review box. Never auto-submit.
- Tap targets 44px minimum. Body text 16px minimum.
- No web fonts. System stack only. Keep the bundle small.
- Skeleton states on every async boundary. Never a blank screen.
- A persistent banner: independent hackathon prototype, not affiliated with
  EPFO or any government body. It stays on every screen.

## Language

- UI chrome strings are hand-written in `src/i18n.ts` for `en` and `hi`.
  Do not machine-translate chrome.
- Only rule explanations pass through the model for language output.

## Stack notes

- Tailwind utility classes only. No component library.
- No localStorage, no sessionStorage. React state only.
