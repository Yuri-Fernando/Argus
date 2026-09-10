# customer-service (Java / Spring Boot)

Bounded context **Customer** (ADR-018). Java 17 + Spring Boot 3, arquitetura
hexagonal (ADR-014): `domain / application / infrastructure / interfaces`.

## O que já está no skeleton

- **Domínio puro** (sem Spring): `Customer` (aggregate root com invariantes +
  domain events), value objects `CustomerId` / `EmailAddress`, events
  `CustomerRegistered` / `CustomerEmailChanged`, ports `CustomerRepository` /
  `DomainEventPublisher`.
- **Aplicação**: `RegisterCustomer` use case (`@Transactional`, outbox de
  eventos).
- **Interface**: `CustomerController` REST (`POST /v1/customers`), DTO com
  Bean Validation.
- **Infra**: adapters in-memory (`InMemoryCustomerRepository`,
  `LoggingDomainEventPublisher`) — placeholders do JPA/Postgres (ADR-020) e
  do publisher `spring-kafka`.
- **Testes**: `CustomerAggregateTest` (JUnit 5) cobrindo as invariantes e a
  emissão de eventos.

## Rodar

```bash
cd services/customer-service
mvn spring-boot:run     # requer JDK 17 + Maven
mvn test
```

## Status

🗺️ **Skeleton estrutural.** `pom.xml` válido (parent Spring Boot 3.3.2),
layout DDD/hexagonal completo e testável. **Não compilado neste ambiente**
(sem JDK 17/Maven). Próximo ciclo: JPA + Postgres (Testcontainers), adapter
Kafka real, Cucumber ligado às features de `tests/bdd/`.
