package com.argus.customer.domain;

import java.time.Instant;

/** Domain event — publicado no tópico Kafka `customer.updated`. */
public record CustomerEmailChanged(String customerId, String newEmail, Instant occurredAt) {}
