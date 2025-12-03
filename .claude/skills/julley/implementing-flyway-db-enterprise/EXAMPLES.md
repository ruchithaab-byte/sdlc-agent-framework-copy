# Flyway Configuration Examples

## Minimal Application.yml
```yaml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    # Baseline only if integrating with existing DB
    baseline-on-migrate: false 
```

## Maven Dependency (PostgreSQL)
```xml
<dependencies>
    <dependency>
        <groupId>org.flywaydb</groupId>
        <artifactId>flyway-core</artifactId>
    </dependency>
    <!-- REQUIRED for Flyway 10+ -->
    <dependency>
        <groupId>org.flywaydb</groupId>
        <artifactId>flyway-postgresql</artifactId>
    </dependency>
</dependencies>
```

## Java Migration Example
```java
public class V002__ComplexUpdate extends BaseJavaMigration {
    public void migrate(Context context) throws Exception {
        try (Statement select = context.getConnection().createStatement()) {
            // Complex logic here
        }
    }
}
```

## Multi-Datasource Configuration
See `templates/multi-datasource-config.template` for the full Java `@Configuration` bean setup.

