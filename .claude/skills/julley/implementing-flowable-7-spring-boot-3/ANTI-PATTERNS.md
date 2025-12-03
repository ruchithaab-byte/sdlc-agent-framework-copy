# Flowable Implementation Anti-Patterns

## Contents
- [AP1: Blocking Transactions](#ap1-blocking-transactions)
- [AP2: javax/jakarta Namespace Mixing](#ap2-javaxjakarta-namespace-mixing)
- [AP3: Missing Async Breaks](#ap3-missing-async-breaks)
- [AP4: Data Hoarding](#ap4-data-hoarding)
- [AP5: Deprecated flowable:class](#ap5-deprecated-flowableclass)

### AP1: Blocking Transactions

**Symptom**: Slow transaction commits, database connection held open, engine thread pool starvation

**Root Cause**: Long-running I/O operations (REST calls, file operations) in synchronous delegates within engine transaction.

**Mitigation**: Use External Worker pattern or async continuation (`flowable:async="true"`). Breaks synchronous path, commits transaction before I/O operation.

**Code Example**:
```java
// ❌ Anti-Pattern: Blocking I/O in synchronous delegate
public void execute(DelegateExecution execution) {
    // Blocks database connection for 5 seconds
    String response = restTemplate.getForObject("http://slow-api", String.class);
}

// ✅ Best Practice: External Worker or async continuation
// External Worker polls and executes outside engine transaction
```

### AP2: javax/jakarta Namespace Mixing

**Symptom**: Class loading errors, `NoClassDefFoundError`, DispatcherServlet initialization failures

**Root Cause**: Mixing libraries compiled against Java EE (javax.*) and Jakarta EE (jakarta.*) on classpath.

**Mitigation**: Mandatory audit of all dependencies. Ensure all libraries are Jakarta EE-compliant. Remove or replace javax.* dependencies.

**Validation**: Check Maven dependency tree: `mvn dependency:tree | grep javax`

### AP3: Missing Async Breaks

**Symptom**: Database lock contention, optimistic locking exceptions, process stalls under load

**Root Cause**: Monolithic synchronous transactions without async breaks. Flowable 7.0.1 synchronous history logging increases transaction duration.

**Mitigation**: Frequent async continuations (`flowable:async="true"`) to break transaction boundaries. Critical before parallel gateway joins.

**Code Example**:
```xml
<!-- ❌ Anti-Pattern: Long synchronous path -->
<serviceTask id="task1" flowable:delegateExpression="${slowDelegate}"/>
<serviceTask id="task2" flowable:delegateExpression="${slowDelegate}"/>
<serviceTask id="task3" flowable:delegateExpression="${slowDelegate}"/>

<!-- ✅ Best Practice: Async breaks -->
<serviceTask id="task1" flowable:async="true" flowable:delegateExpression="${slowDelegate}"/>
<serviceTask id="task2" flowable:async="true" flowable:delegateExpression="${slowDelegate}"/>
<serviceTask id="task3" flowable:async="true" flowable:delegateExpression="${slowDelegate}"/>
```

### AP4: Data Hoarding

**Symptom**: Large `ACT_RU_VARIABLE` table, slow history queries, prolonged database lock times

**Root Cause**: Storing large payloads (full JSON API responses, large lists, binary documents) as persistent process variables.

**Mitigation**: Apply Transient Variable Doctrine. Use `setTransientVariable()` for temporary data. Store only references (IDs) for large documents.

**Code Example**:
```java
// ❌ Anti-Pattern: Large payload as persistent variable
execution.setVariable("apiResponse", largeJsonObject); // 10MB JSON

// ✅ Best Practice: Transient variable or reference only
execution.setTransientVariable("apiResponse", largeJsonObject);
execution.setVariable("documentId", documentId); // Store only ID
```

### AP5: Deprecated flowable:class

**Symptom**: No dependency injection in delegates, manual service location, tightly coupled code

**Root Cause**: Using deprecated `flowable:class` attribute instead of `flowable:delegateExpression`. Bypasses Spring container.

**Mitigation**: Migrate to Delegate Expression pattern. Annotate delegate with `@Component`, reference via `flowable:delegateExpression="${beanName}"`.

**Code Example**:
```xml
<!-- ❌ Anti-Pattern: Deprecated class attribute -->
<serviceTask id="task1" flowable:class="com.example.MyDelegate"/>

<!-- ✅ Best Practice: Delegate Expression -->
<serviceTask id="task1" flowable:delegateExpression="${myDelegate}"/>
```

