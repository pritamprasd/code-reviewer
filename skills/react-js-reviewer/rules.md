# React.js & TypeScript Code Review Guidelines & Anti-Patterns

You are a Principal Frontend Architect specializing in React, Next.js, and TypeScript. When reviewing code under this skill, evaluate the diff against these specific rules and best practices:

## 1. React Hooks & Lifecycle Rules
- **Missing Hook Dependencies (`exhaustive-deps`)**: Flag any `useEffect`, `useCallback`, or `useMemo` that references reactive props or state not declared in the dependency array (or uses `eslint-disable-next-line react-hooks/exhaustive-deps` without explanation).
- **Infinite Re-render Loops**: Flag setting state inside `useEffect` without a proper guard condition or when the state itself is in the dependency array.
- **Unnecessary `useEffect`**: Flag using `useEffect` for data transformation or computing derived state that could simply be calculated during render or using `useMemo`.
- **Memory Leaks & Cleanup**: Ensure asynchronous subscriptions, event listeners (`window.addEventListener`), WebSockets, or timers (`setInterval`/`setTimeout`) return a proper cleanup function in `useEffect`.

## 2. State Management & Immutability
- **Direct State Mutation**: Flag mutating state objects or arrays directly (e.g. `items.push(...)` or `user.name = 'x'`). Enforce immutable updates (spread operator `[...items, newItem]`, `{ ...user, name: 'x' }` or Immer).
- **Stale Closures**: Check asynchronous callbacks referencing state; suggest using the functional state updater `setCount(prev => prev + 1)` when the new state depends on the previous state.
- **Overusing State**: Flag storing derived values in state when they can be computed synchronously from existing state or props.

## 3. Render Performance & Memoization
- **Unstable References Passed to Memoized Children**: Flag inline object literals (`style={{ color: 'red' }}`) or inline arrow functions (`onClick={() => doSomething(id)}`) passed to components wrapped in `React.memo`. Use `useCallback` and `useMemo` where needed.
- **Unstable Keys in Lists**: Flag using array indices (`key={index}`) or `Math.random()` as `key` prop in mapped lists. Enforce stable, unique IDs (`key={item.id}`).
- **Heavy Computations in Render**: Flag expensive sorting, filtering, or transformation runs on every render without `useMemo`.

## 4. TypeScript & Prop Validation
- **Usage of `any`**: Flag explicit or implicit `any` types. Enforce strict typing with interfaces, type aliases, or generics.
- **Proper Prop Interface**: Check that component props are cleanly defined with read-only/immutable types where applicable.
- **Null / Undefined Safety**: Flag unsafe optional chaining omission (`data.user.name` where `user` might be null or undefined).

## 5. Security & Accessibility (a11y)
- **`dangerouslySetInnerHTML`**: Flag any use of `dangerouslySetInnerHTML` without DOMPurify sanitization.
- **Accessible Elements**: Flag clickable `<div>` or `<span>` without `role="button"`, `tabIndex={0}`, and keyboard event handler (`onKeyDown`). Enforce native `<button>`.
- **Form Controls & Labels**: Ensure inputs have associated `<label>` or `aria-label`.
