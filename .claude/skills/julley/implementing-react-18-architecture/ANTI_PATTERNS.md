# Anti-Patterns

## 1. Legacy ReactDOM.render Usage

**Description**: Using ReactDOM.render instead of createRoot API prevents concurrent rendering benefits.

**Impact**: Blocks React 18 scheduler, prevents useTransition/useDeferredValue from working, no concurrent rendering benefits.

**Workaround**: Use createRoot API for React 18+ initialization.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Legacy API
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));
```

**Workaround Code**:
```typescript
// ✅ Good: Modern API
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root')!);
root.render(<App />);
```

## 2. Business Logic in Atoms

**Description**: Placing complex business logic or stateful operations in atomic components breaks reusability principle.

**Impact**: Breaks reusability principle, creates maintenance debt, violates separation of concerns, makes Atoms tightly coupled to business logic.

**Workaround**: Keep Atoms purely presentational, move logic to Organisms or Custom Hooks.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Business logic in Atom
function Button({ userId }: { userId: string }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetchUser(userId).then(setUser); // Business logic in Atom
  }, [userId]);
  
  return <button>{user?.name || 'Loading'}</button>;
}
```

**Workaround Code**:
```typescript
// ✅ Good: Atom is presentational only
function Button({ label, onClick }: { label: string; onClick: () => void }) {
  return <button onClick={onClick}>{label}</button>;
}

// Logic in Custom Hook or Organism
function useUser(userId: string) {
  const [user, setUser] = useState(null);
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  return user;
}
```

## 3. Everything in App State Lifting

**Description**: Lifting too much state to root App component unnecessarily forces wide re-renders.

**Impact**: Forces wide, costly re-renders across entire application, performance degradation, unnecessary component updates.

**Workaround**: Colocate state in lowest common ancestor, use Context or external state for truly shared state.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: All state in App
function App() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  const [cart, setCart] = useState([]);
  const [notifications, setNotifications] = useState([]);
  // ... many more states
  
  return (
    <div>
      <Header user={user} theme={theme} />
      <Sidebar cart={cart} notifications={notifications} />
      <MainContent user={user} cart={cart} />
    </div>
  );
}
```

**Workaround Code**:
```typescript
// ✅ Good: State colocated in lowest common ancestor
function CartSection() {
  const [cart, setCart] = useState([]); // Colocated
  return <CartDisplay cart={cart} />;
}

function App() {
  const [user, setUser] = useState(null); // Only truly global state
  return (
    <AuthProvider value={{ user, setUser }}>
      <Header />
      <CartSection />
      <MainContent />
    </AuthProvider>
  );
}
```

## 4. Context for High-Frequency Updates

**Description**: Using Context API for frequently changing data (form inputs, live dashboards, real-time updates) causes performance issues.

**Impact**: Forces unnecessary re-renders of all consumers, severe performance bottlenecks, UI lag.

**Workaround**: Use subscription-based libraries (Zustand, Jotai) for high-frequency state updates.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Context for high-frequency updates
const FormContext = createContext();

function FormProvider({ children }) {
  const [formData, setFormData] = useState({}); // Changes frequently
  return (
    <FormContext.Provider value={{ formData, setFormData }}>
      {children} {/* All children re-render on every keystroke */}
    </FormContext.Provider>
  );
}
```

**Workaround Code**:
```typescript
// ✅ Good: Zustand for high-frequency updates
import { create } from 'zustand';

const useFormStore = create((set) => ({
  formData: {},
  updateField: (field, value) => set((state) => ({
    formData: { ...state.formData, [field]: value }
  })),
}));

// Only components using specific fields re-render
```

## 5. Stale Closures in useEffect

**Description**: Functions capturing outdated state/props from previous render cycles in useEffect or async callbacks.

**Impact**: Asynchronous bugs, logic operating on outdated values, incorrect behavior, race conditions.

**Workaround**: Use functional state updates (setState(prev => ...)), strict dependency arrays, stabilize with useCallback/useMemo.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Stale closure
function Counter() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCount(count + 1); // Uses stale count value
    }, 1000);
    return () => clearInterval(interval);
  }, []); // Missing count in dependencies
}
```

**Workaround Code**:
```typescript
// ✅ Good: Functional update
function Counter() {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCount(prev => prev + 1); // Always uses latest state
    }, 1000);
    return () => clearInterval(interval);
  }, []); // No dependency needed with functional update
}
```

## 6. Inline Component Creation

**Description**: Creating components inside render function of another component causes remounting.

**Impact**: Forces component remounting on every render, state loss, focus loss, unnecessary side effects, performance degradation.

**Workaround**: Define components outside parent's render function to maintain stable references.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Component defined inside render
function ParentComponent() {
  const [value, setValue] = useState('');
  
  const ChildComponent = () => <div>{value}</div>; // New component on every render
  
  return <ChildComponent />; // Causes remounting
}
```

**Workaround Code**:
```typescript
// ✅ Good: Component defined outside
const ChildComponent = ({ value }: { value: string }) => <div>{value}</div>;

function ParentComponent() {
  const [value, setValue] = useState('');
  return <ChildComponent value={value} />; // Stable reference
}
```

## 7. Prop Drilling

**Description**: Manually passing data through multiple intermediate components that don't need it.

**Impact**: High coupling, reduced maintainability, verbose code, fragile component structure, difficult refactoring.

**Workaround**: Use Context API for global data, improve component composition (pass elements as props), use state management libraries.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Prop drilling
function App() {
  const [user, setUser] = useState(null);
  return <Layout user={user} />; // user not used in Layout
}

function Layout({ user }) {
  return <Header user={user} />; // user not used in Header
}

function Header({ user }) {
  return <UserMenu user={user} />; // Finally used here
}
```

**Workaround Code**:
```typescript
// ✅ Good: Context API
const UserContext = createContext();

function App() {
  const [user, setUser] = useState(null);
  return (
    <UserContext.Provider value={user}>
      <Layout />
    </UserContext.Provider>
  );
}

function UserMenu() {
  const user = useContext(UserContext); // Direct access
  return <div>{user?.name}</div>;
}
```

## 8. Premature/Excessive Memoization

**Description**: Overusing useMemo/useCallback on cheap components or frequently changing props.

**Impact**: Overhead cost of dependency comparison negates minimal rendering savings, unnecessary complexity, harder to maintain.

**Workaround**: Only memoize expensive computations and stable function references, prioritize state colocation.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Premature memoization
function SimpleComponent({ name }: { name: string }) {
  const memoizedName = useMemo(() => name.toUpperCase(), [name]); // Unnecessary
  const handleClick = useCallback(() => console.log(name), [name]); // Unnecessary
  
  return <button onClick={handleClick}>{memoizedName}</button>;
}
```

**Workaround Code**:
```typescript
// ✅ Good: Memoize only expensive operations
function ExpensiveComponent({ items }: { items: Item[] }) {
  const sortedItems = useMemo(() => {
    return items.sort((a, b) => a.price - b.price); // Expensive operation
  }, [items]);
  
  return <div>{sortedItems.map(item => <div key={item.id}>{item.name}</div>)}</div>;
}
```

## 9. Manual useEffect Data Fetching

**Description**: Using useEffect for server state management (data fetching, caching, synchronization, error handling).

**Impact**: Redundant manual management, missing features (automatic caching, stale data invalidation, error recovery), boilerplate code.

**Workaround**: Use specialized libraries (React Query, RTK Query) for server state management.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Manual data fetching
function ProductsList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(setProducts)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []); // Missing caching, refetching, error recovery
}
```

**Workaround Code**:
```typescript
// ✅ Good: React Query
import { useQuery } from '@tanstack/react-query';

function ProductsList() {
  const { data: products, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => fetch('/api/products').then(res => res.json()),
  }); // Automatic caching, refetching, error handling
}
```

## 10. Direct Server Component Import into Client Component

**Description**: Importing Server Components directly into Client Component modules (Next.js App Router).

**Impact**: Breaks React Server Components architecture, runtime errors, hydration mismatches.

**Workaround**: Use component interleaving (pass SC as children prop to CC).

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Direct SC import into CC
'use client';
import { ServerComponent } from './ServerComponent'; // Error

function ClientComponent() {
  return <ServerComponent />; // Cannot import SC into CC
}
```

**Workaround Code**:
```typescript
// ✅ Good: Component interleaving
'use client';
function ClientComponent({ children }: { children: ReactNode }) {
  return <div>{children}</div>;
}

// Server Component
import { ClientComponent } from './ClientComponent';
import { ServerData } from './ServerData';

export default function Page() {
  return (
    <ClientComponent>
      <ServerData /> {/* SC passed as children */}
    </ClientComponent>
  );
}
```

## 11. Non-Serializable Props

**Description**: Passing non-serializable data (functions, class instances, Date objects) to Server Components.

**Impact**: Serialization errors, hydration mismatches, runtime failures.

**Workaround**: Pass only serializable data (primitives, plain objects), use Server Actions for mutations.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Non-serializable props
function ServerComponent({ onClick, date }: { onClick: () => void; date: Date }) {
  return <button onClick={onClick}>{date.toISOString()}</button>; // Error
}
```

**Workaround Code**:
```typescript
// ✅ Good: Serializable props
function ServerComponent({ dateString }: { dateString: string }) {
  const date = new Date(dateString); // Deserialize in component
  return <div>{date.toISOString()}</div>;
}

// Pass serialized data
<ServerComponent dateString={date.toISOString()} />
```

## 12. Missing Validation in Server Actions

**Description**: Server Actions without input validation and authorization checks.

**Impact**: Security vulnerabilities, data corruption, unauthorized access, injection attacks.

**Workaround**: Always validate and authorize in Server Actions before mutations, use schema validation libraries.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: No validation
'use server';
export async function createPost(formData: FormData) {
  const title = formData.get('title');
  await db.posts.create({ title }); // No validation, no auth check
}
```

**Workaround Code**:
```typescript
// ✅ Good: Validation and authorization
'use server';
import { z } from 'zod';

const postSchema = z.object({ title: z.string().min(1).max(100) });

export async function createPost(formData: FormData) {
  const user = await getCurrentUser();
  if (!user) throw new Error('Unauthorized');
  
  const validated = postSchema.safeParse({ title: formData.get('title') });
  if (!validated.success) throw new Error('Validation failed');
  
  await db.posts.create({ title: validated.data.title, userId: user.id });
}
```

## 13. Wrapper Hell (Excessive HOC Nesting)

**Description**: Deeply nested Higher-Order Components creating complex component trees.

**Impact**: Difficult debugging, prop namespace collisions, reduced readability, performance overhead, hard to trace data flow.

**Workaround**: Prefer Custom Hooks for reusable logic, use HOCs sparingly for cross-cutting concerns only.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Wrapper hell
const EnhancedComponent = withTheme(
  withAuth(
    withRouter(
      withAnalytics(Component) // Deep nesting
    )
  )
);
```

**Workaround Code**:
```typescript
// ✅ Good: Custom Hooks
function Component() {
  const theme = useTheme();
  const user = useAuth();
  const router = useRouter();
  const analytics = useAnalytics();
  // Clean, composable logic
}
```

## 14. Global State Sprawl

**Description**: Moving too much state to global stores unnecessarily.

**Impact**: Reduced performance, increased complexity, harder to reason about state flow, unnecessary re-renders.

**Workaround**: Keep state local (useState, useReducer), only elevate to global when truly shared across distant components.

**Anti-Pattern Code**:
```typescript
// ❌ Bad: Global state sprawl
const useStore = create((set) => ({
  count: 0,
  name: '',
  theme: 'light',
  cart: [],
  notifications: [],
  user: null,
  // ... everything in global store
}));
```

**Workaround Code**:
```typescript
// ✅ Good: Local state with selective global
function Counter() {
  const [count, setCount] = useState(0); // Local state
  return <div>{count}</div>;
}

// Only truly shared state in global store
const useAuthStore = create((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
```

