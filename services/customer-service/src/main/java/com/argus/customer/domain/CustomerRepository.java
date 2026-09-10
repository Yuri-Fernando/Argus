package com.argus.customer.domain;

import java.util.Optional;

/** Port de persistência (hexagonal) — implementado em infrastructure/. */
public interface CustomerRepository {
    void save(Customer customer);
    Optional<Customer> findById(CustomerId id);
}
