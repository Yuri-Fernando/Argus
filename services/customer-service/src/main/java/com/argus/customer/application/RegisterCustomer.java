package com.argus.customer.application;

import com.argus.customer.domain.Customer;
import com.argus.customer.domain.CustomerId;
import com.argus.customer.domain.CustomerRepository;
import com.argus.customer.domain.DomainEventPublisher;
import com.argus.customer.domain.EmailAddress;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Use case — cria o agregado, persiste e publica os domain events (outbox). */
@Service
public class RegisterCustomer {

    private final CustomerRepository repository;
    private final DomainEventPublisher publisher;

    public RegisterCustomer(CustomerRepository repository, DomainEventPublisher publisher) {
        this.repository = repository;
        this.publisher = publisher;
    }

    @Transactional
    public CustomerId handle(String name, String email) {
        Customer customer = Customer.register(CustomerId.newId(), name, new EmailAddress(email));
        repository.save(customer);
        publisher.publishAll(customer.pullDomainEvents());
        return customer.id();
    }
}
