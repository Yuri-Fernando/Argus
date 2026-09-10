package com.argus.customer.infrastructure;

import com.argus.customer.domain.Customer;
import com.argus.customer.domain.CustomerId;
import com.argus.customer.domain.CustomerRepository;
import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Adapter de persistência em memória — placeholder do repositório JPA/Postgres
 * (database-per-service, ADR-020). Mantém o serviço executável no skeleton.
 */
@Repository
public class InMemoryCustomerRepository implements CustomerRepository {

    private final Map<String, Customer> store = new ConcurrentHashMap<>();

    @Override
    public void save(Customer customer) {
        store.put(customer.id().value(), customer);
    }

    @Override
    public Optional<Customer> findById(CustomerId id) {
        return Optional.ofNullable(store.get(id.value()));
    }
}
