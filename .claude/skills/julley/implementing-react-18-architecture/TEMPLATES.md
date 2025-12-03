# Code Templates

## Template 1: TypeScript Functional Component (RFC)
```typescript
import React, { FC } from 'react';

interface ButtonPrimaryProps {
  label: string;
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
  isDisabled?: boolean;
}

const ButtonPrimary: FC<ButtonPrimaryProps> = ({ label, onClick, isDisabled = false }) => {
  return (
    <button className="btn-primary" onClick={onClick} disabled={isDisabled}>
      {label}
    </button>
  );
};

export default ButtonPrimary;
```

## Template 2: Context Provider with Safe Consumption Hook
```typescript
import { createContext, useContext, useState, FC, ReactNode } from 'react';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const login = (userData: User) => setUser(userData);
  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

## Template 3: Custom Hook (useDocumentTitle)
```typescript
import { useEffect, useRef } from 'react';

export function useDocumentTitle(title: string, prevailOnUnmount = false) {
  const defaultTitle = useRef(document.title);

  useEffect(() => {
    document.title = title;
  }, [title]);

  useEffect(() => {
    return () => {
      if (!prevailOnUnmount) {
        document.title = defaultTitle.current;
      }
    };
  }, [prevailOnUnmount]);
}
```

## Template 4: useDeferredValue Search Filter
```typescript
import { useState, useDeferredValue } from 'react';

function DeferredSearchComponent() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      {query !== deferredQuery && <p>Loading results...</p>}
      <HeavyList query={deferredQuery} />
    </div>
  );
}
```

## Template 5: Compound Component Pattern
```typescript
import { createContext, useContext, useState, FC, ReactNode } from 'react';

interface TabsContextType {
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

export const Tabs: FC<{ children: ReactNode }> = ({ children }) => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  return (
    <TabsContext.Provider value={{ selectedIndex, setSelectedIndex }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
};

Tabs.Panel = function TabsPanel({ index, children }: { index: number; children: ReactNode }) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tabs.Panel must be used within Tabs');
  return context.selectedIndex === index ? <div>{children}</div> : null;
};
```

## Template 6: Zustand Store Setup
```typescript
import { create } from 'zustand';

interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
}

export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}));
```

## Template 7: React.memo Optimization
```typescript
import { memo } from 'react';

interface ProductCardProps {
  product: { id: string; name: string };
}

export const ProductCard = memo(function ProductCard({ product }: ProductCardProps) {
  return <div>{product.name}</div>;
});
```

## Template 8: Code Splitting with Suspense
```typescript
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

## Template 9: Error Boundary Class Component
```typescript
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

## Template 10: Portal Implementation
```typescript
import { createPortal } from 'react-dom';

function Modal({ children, isOpen }: { children: ReactNode; isOpen: boolean }) {
  if (!isOpen) return null;
  return createPortal(
    <div className="modal-overlay">
      <div className="modal-content">{children}</div>
    </div>,
    document.body
  );
}
```

