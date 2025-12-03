package com.example.app.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    private final UserService userService;
    
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserRecord createUser(@Valid @RequestBody UserCreationRequestDTO request) {
        return userService.saveNewUser(request);
    }
    
    @GetMapping("/{id}")
    public UserRecord getUserById(@PathVariable Long id) {
        return userService.findById(id);
    }
}

