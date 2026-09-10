package com.argus.customer.domain;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Aggregate root do bounded context Customer.
 * Mantém suas invariantes e registra domain events; não conhece infraestrutura.
 */
public class Customer {

    private final CustomerId id;
    private String name;
    private EmailAddress email;
    private long version;
    private final List<Object> domainEvents = new ArrayList<>();

    private Customer(CustomerId id, String name, EmailAddress email) {
        this.id = Objects.requireNonNull(id);
        this.name = requireName(name);
        this.email = Objects.requireNonNull(email);
        this.version = 0L;
    }

    public static Customer register(CustomerId id, String name, EmailAddress email) {
        Customer c = new Customer(id, name, email);
        c.domainEvents.add(new CustomerRegistered(id.value(), email.value(), Instant.now()));
        return c;
    }

    public void changeEmail(EmailAddress newEmail) {
        Objects.requireNonNull(newEmail);
        if (newEmail.equals(this.email)) {
            return;
        }
        this.email = newEmail;
        this.version++;
        this.domainEvents.add(new CustomerEmailChanged(id.value(), newEmail.value(), Instant.now()));
    }

    private static String requireName(String name) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("nome do cliente é obrigatório");
        }
        return name;
    }

    public CustomerId id() { return id; }
    public String name() { return name; }
    public EmailAddress email() { return email; }
    public long version() { return version; }

    public List<Object> pullDomainEvents() {
        List<Object> copy = List.copyOf(domainEvents);
        domainEvents.clear();
        return copy;
    }
}
