package com.argus.customer.domain;

import java.util.Objects;
import java.util.regex.Pattern;

/** Value object — e-mail validado. */
public record EmailAddress(String value) {
    private static final Pattern RE = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$");

    public EmailAddress {
        Objects.requireNonNull(value);
        if (!RE.matcher(value).matches()) {
            throw new IllegalArgumentException("e-mail inválido: " + value);
        }
    }
}
