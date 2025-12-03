# Flowable Implementation Examples

## Real-World Examples

### Example 1: Payment Processing with External Worker

**Scenario**: Payment processing workflow using External Worker for decoupled execution.

**Worker Implementation**:
```java
@Component
public class PaymentProcessingWorker {
    @FlowableWorker(topic = "paymentTopic", lockDuration = 60000)
    public WorkerResult processPayment(AcquiredExternalWorkerJob job, WorkerResultBuilder resultBuilder) {
        String orderId = job.getVariable("orderId");
        // Call payment service
        PaymentResponse response = paymentClient.process(orderId);
        
        if (response.isSuccessful()) {
            return resultBuilder.success()
                   .variable("confirmationId", response.getConfirmationId());
        } else {
            return resultBuilder.failure()
                   .message("Payment processing failed");
        }
    }
}
```

**Configuration**:
```properties
flowable.external-worker.base-url=http://localhost:8080/flowable-rest/service
flowable.external-worker.concurrency=10
```

**Key Points**: Worker polls for jobs, executes payment logic, signals success/failure with result variables. Engine remains decoupled from payment service latency.

### Example 2: Order Saga with Compensation

**Scenario**: E-commerce order processing coordinating payment, inventory, and shipping with compensation on failure.

**BPMN Structure**:
```xml
<process id="orderSaga">
  <startEvent id="start"/>
  
  <serviceTask id="processPayment" 
               flowable:delegateExpression="${paymentDelegate}"/>
  <boundaryEvent id="paymentError" attachedToRef="processPayment">
    <errorEventDefinition errorRef="paymentFailed"/>
  </boundaryEvent>
  
  <serviceTask id="reserveInventory" 
               flowable:delegateExpression="${inventoryDelegate}"/>
  <boundaryEvent id="inventoryError" attachedToRef="reserveInventory">
    <errorEventDefinition errorRef="inventoryFailed"/>
  </boundaryEvent>
  
  <serviceTask id="compensatePayment" 
               flowable:isForCompensation="true"
               flowable:delegateExpression="${refundDelegate}"/>
  
  <endEvent id="end"/>
</process>
```

**Delegate Implementation**:
```java
@Component("paymentDelegate")
public class PaymentDelegate implements JavaDelegate {
    @Autowired
    private PaymentService paymentService;
    
    @Override
    public void execute(DelegateExecution execution) {
        String orderId = (String) execution.getVariable("orderId");
        PaymentResult result = paymentService.process(orderId);
        
        if (!result.isSuccessful()) {
            throw new BpmnError("paymentFailed", "Payment processing failed");
        }
        
        execution.setVariable("paymentId", result.getPaymentId());
    }
}
```

**Key Points**: Each Service Task has Boundary Error Event. Compensation handler (`compensatePayment`) marked with `flowable:isForCompensation="true"`. On failure, compensation automatically triggered.

