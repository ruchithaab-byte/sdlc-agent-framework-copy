package com.example.app.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record UserRecord(Long id, String firstName, String email) {}

public record UserCreationRequestDTO(
    @NotBlank String firstName,
    @Email String email
) {}

