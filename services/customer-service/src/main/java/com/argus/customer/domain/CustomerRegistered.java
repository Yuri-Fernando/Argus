package com.argus.customer.domain;

import java.time.Instant;

/** Domain event — publicado no tópico Kafka `customer.created`. */
public record CustomerRegistered(String customerId, String email, Instant occurredAt) {}
