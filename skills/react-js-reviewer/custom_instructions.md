# React.js Custom Team Instructions

- **Data Fetching**: Prefer React Query (TanStack Query) or custom hook over raw `fetch()` or `axios` calls directly inside `useEffect`.
- **State Management**: Prefer Zustand or React Context for shared state over deep prop-drilling (> 3 levels).
- **TypeScript**: No explicit or implicit `any`. Use strict generic types for API responses and component props.
- **Styling**: Ensure CSS class names follow project conventions (e.g. Tailwind or CSS Modules).
