package com.argus.customer;

import com.argus.customer.domain.Customer;
import com.argus.customer.domain.CustomerEmailChanged;
import com.argus.customer.domain.CustomerId;
import com.argus.customer.domain.CustomerRegistered;
import com.argus.customer.domain.EmailAddress;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CustomerAggregateTest {

    @Test
    void register_emits_CustomerRegistered_event() {
        Customer c = Customer.register(CustomerId.newId(), "Ada Lovelace", new EmailAddress("ada@example.com"));
        List<Object> events = c.pullDomainEvents();
        assertThat(events).hasSize(1);
        assertThat(events.get(0)).isInstanceOf(CustomerRegistered.class);
    }

    @Test
    void changeEmail_bumps_version_and_emits_event() {
        Customer c = Customer.register(CustomerId.newId(), "Ada", new EmailAddress("ada@example.com"));
        c.pullDomainEvents(); // descarta o de registro
        c.changeEmail(new EmailAddress("ada.l@example.com"));
        assertThat(c.version()).isEqualTo(1L);
        assertThat(c.pullDomainEvents()).singleElement().isInstanceOf(CustomerEmailChanged.class);
    }

    @Test
    void changeEmail_to_same_value_is_noop() {
        Customer c = Customer.register(CustomerId.newId(), "Ada", new EmailAddress("ada@example.com"));
        c.pullDomainEvents();
        c.changeEmail(new EmailAddress("ada@example.com"));
        assertThat(c.version()).isZero();
        assertThat(c.pullDomainEvents()).isEmpty();
    }

    @Test
    void invalid_email_is_rejected() {
        assertThatThrownBy(() -> new EmailAddress("not-an-email"))
            .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void blank_name_is_rejected() {
        assertThatThrownBy(() -> Customer.register(CustomerId.newId(), "  ", new EmailAddress("a@b.co")))
            .isInstanceOf(IllegalArgumentException.class);
    }
}
