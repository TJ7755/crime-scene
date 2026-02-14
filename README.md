# Case Dossier Front-End

Production-oriented React + TypeScript + Vite front-end for a deterministic investigation engine.  
The UI is intentionally a thin client over engine-provided visible state and discrete actions.

## Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Vitest + Testing Library (smoke test)

## Setup

1. Install dependencies:

```bash
npm install
```

2. Start development server:

```bash
npm run dev
```

3. Build for production:

```bash
npm run build
```

4. Preview production build:

```bash
npm run preview
```

## Adapter Modes

This project supports two adapter modes in `src/api/engineAdapter.ts`.

- Mock adapter (default): deterministic local demo.
- Live adapter: sends `fetch()` requests to the Python engine endpoints.

### Use Live Engine

Set environment variables (for example in `.env.local`):

```bash
VITE_USE_MOCK=false
VITE_ENGINE_API_BASE=http://localhost:8000
```

When live mode is enabled, the front-end calls:

- `GET /api/visible_state`
- `GET /api/actions`
- `POST /api/apply_action` with `{ action_id, params }`

## Deterministic Mock Demo

Mock mode uses deterministic seeded data via query parameter:

- Open `http://localhost:5173/?seed=42` for reproducible state.
- The same seed and action sequence produce the same results.

The mock adapter also provides in-memory case page save/load behavior so the UI can demonstrate snapshot switching without backend storage.

## Test

Run the smoke test:

```bash
npm run test
```
