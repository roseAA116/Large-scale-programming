# Test Report

Date: 2026-07-12

## Commands

```powershell
cd backend
python -m pytest
```

Result: 34 passed, 1 warning.

```powershell
cd frontend
npm run build
```

Result: TypeScript build and Vite production build passed.

```powershell
cd frontend
npm run test:e2e
```

Result: Playwright browser smoke tests cover dashboard, summary generation, multi-course planning analysis, and admin operations pages with mocked API responses.

## Covered Areas

- Authentication, JWT, logout invalidation
- Material upload validation, parsing, chunking, embeddings
- Search, Agent answer generation, answer citations
- Stage 7 API acceptance flow for citations
- Study plan generation and plan item status updates
- Intelligent task preview and task creation from plan items
- Task management status transitions
- Course summary generation from READY chunks
- Multi-course planning analysis and allocation
- Browser-level frontend smoke coverage for key routes

## Residual Risk

Browser tests currently use mocked API responses. A later CI job can add live backend seeded-data E2E if deployment realism is required.
