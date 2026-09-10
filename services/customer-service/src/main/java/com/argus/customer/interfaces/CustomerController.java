package com.argus.customer.interfaces;

import com.argus.customer.application.RegisterCustomer;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;

/** Interface REST — camada fina: valida o DTO, chama o use case, mapeia HTTP. */
@RestController
@RequestMapping("/v1/customers")
public class CustomerController {

    private final RegisterCustomer registerCustomer;

    public CustomerController(RegisterCustomer registerCustomer) {
        this.registerCustomer = registerCustomer;
    }

    public record RegisterBody(@NotBlank String name, @Email @NotBlank String email) {}

    @PostMapping
    public ResponseEntity<Void> register(@RequestBody RegisterBody body) {
        var id = registerCustomer.handle(body.name(), body.email());
        return ResponseEntity.created(URI.create("/v1/customers/" + id.value())).build();
    }
}
