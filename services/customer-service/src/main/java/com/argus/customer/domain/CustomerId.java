package com.argus.customer.domain;

import java.util.Objects;
import java.util.UUID;

/** Value object — identidade opaca do cliente. */
public record CustomerId(String value) {
    public CustomerId {
        Objects.requireNonNull(value);
        if (value.isBlank()) {
            throw new IllegalArgumentException("CustomerId não pode ser vazio");
        }
    }

    public static CustomerId newId() {
        return new CustomerId("CUST-" + UUID.randomUUID());
    }
}
