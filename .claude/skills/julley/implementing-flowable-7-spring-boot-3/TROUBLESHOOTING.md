# Flowable Implementation Troubleshooting

## Error Handling Guide

### Jakarta EE Migration Errors

**Symptom**: Class loading conflicts, `NoClassDefFoundError`, DispatcherServlet initialization failures.

**Cause**: Mixing `javax.*` (Java EE) and `jakarta.*` (Jakarta EE) namespaces on the classpath.

**Resolution**: 
1. Audit dependencies: `mvn dependency:tree | grep javax`
2. Replace `javax.*` libraries with Jakarta-compliant versions (e.g., Hibernate 6+, Tomcat 10+, Spring Boot 3+).

### Transaction Errors

**Symptom**: `FlowableOptimisticLockingException`, transaction timeouts.

**Cause**: 
- Concurrent modification of the same process instance.
- Long-running synchronous transactions holding database locks.

**Resolution**: 
- Add async continuation (`flowable:async="true"`) before parallel joins.
- Increase frequency of async breaks to shorten transaction windows.
- Switch to External Worker pattern for long-running tasks.

### Variable Errors

**Symptom**: Performance degradation, slow history queries, `ACT_RU_VARIABLE` table bloat.

**Cause**: Storing large payloads (JSON, binaries) as persistent variables.

**Resolution**: 
- Apply Transient Variable Doctrine.
- Use `execution.setTransientVariable()` for temporary data.
- Store only foreign keys/IDs in process variables; keep data in business tables.

### Delegate Errors

**Symptom**: `NullPointerException` when accessing injected fields in delegates.

**Cause**: Delegate class instantiated manually (e.g., via `new MyDelegate()` or `flowable:class`) instead of being managed by Spring.

**Resolution**: 
- Use Delegate Expression pattern.
- Annotate class with `@Component` or `@Service`.
- Reference in BPMN with `flowable:delegateExpression="${beanName}"`.

