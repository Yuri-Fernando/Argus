package com.argus.customer.domain;

import java.util.List;

/** Port de mensageria — implementado por um adapter Kafka em infrastructure/. */
public interface DomainEventPublisher {
    void publishAll(List<Object> events);
}
