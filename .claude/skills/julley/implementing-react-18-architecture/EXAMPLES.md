# Real-World Examples

## Example 1: Deferred Search with Heavy List Rendering

**Use Case**: Search input that filters a large list without causing input lag.

```typescript
import { useState, useDeferredValue, useMemo } from 'react';

function SearchPage() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  
  const filteredItems = useMemo(() => {
    return largeList.filter(item => 
      item.name.toLowerCase().includes(deferredQuery.toLowerCase())
    );
  }, [deferredQuery]);

  return (
    <div>
      <input 
        value={query} 
        onChange={(e) => setQuery(e.target.value)} 
        placeholder="Search..."
      />
      {query !== deferredQuery && <p>Searching...</p>}
      <ItemList items={filteredItems} />
    </div>
  );
}
```

## Example 2: Compound Tabs Component

**Use Case**: Tabs component with implicit state sharing between parent and children.

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

Tabs.List = function TabsList({ children }: { children: ReactNode }) {
  return <div className="tabs-list">{children}</div>;
};

Tabs.Tab = function Tab({ index, children }: { index: number; children: ReactNode }) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tab must be used within Tabs');
  
  return (
    <button
      onClick={() => context.setSelectedIndex(index)}
      className={context.selectedIndex === index ? 'active' : ''}
    >
      {children}
    </button>
  );
};

Tabs.Panel = function TabsPanel({ index, children }: { index: number; children: ReactNode }) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabsPanel must be used within Tabs');
  return context.selectedIndex === index ? <div>{children}</div> : null;
};

// Usage
<Tabs>
  <Tabs.List>
    <Tabs.Tab index={0}>About</Tabs.Tab>
    <Tabs.Tab index={1}>Posts</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel index={0}>About content</Tabs.Panel>
  <Tabs.Panel index={1}>Posts content</Tabs.Panel>
</Tabs>
```

