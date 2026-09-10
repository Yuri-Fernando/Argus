package com.argus.customer.infrastructure;

import com.argus.customer.domain.DomainEventPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Adapter de mensageria — placeholder do publisher Kafka (spring-kafka).
 * No serviço real, serializa cada event para o tópico correspondente
 * (`customer.created`, `customer.updated`) validando contra o JSON Schema
 * em `platform/messaging/schemas/`.
 */
@Component
public class LoggingDomainEventPublisher implements DomainEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(LoggingDomainEventPublisher.class);

    @Override
    public void publishAll(List<Object> events) {
        events.forEach(e -> log.info("domain-event {}", e));
    }
}
