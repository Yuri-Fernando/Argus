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
./mvnw verify            # compila + roda os 5 testes JUnit (requer só JDK 17)
./mvnw spring-boot:run   # sobe o serviço em :8081
```

O Maven wrapper (`./mvnw` / `mvnw.cmd`) está incluído — não precisa de Maven
instalado, só de um JDK 17.

## Status

✅ **Compila e testa.** `mvn verify` com JDK 17 (Temurin): parent Spring Boot
3.3.2, layout DDD/hexagonal, **5 testes JUnit** (`CustomerAggregateTest`)
verdes cobrindo invariantes do agregado e emissão de domain events. Job
`java-customer-service` no workflow `.github/workflows/enterprise-v2.yml`.

Próximo ciclo: JPA + Postgres (Testcontainers), adapter Kafka real
(`spring-kafka`), Cucumber ligado às features de `tests/bdd/`.
