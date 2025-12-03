package com.example.app.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "app_user")
public class UserEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String firstName;
    private String email;
    
    protected UserEntity() {}
    
    public UserEntity(String firstName, String email) {
        this.firstName = firstName;
        this.email = email;
    }
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getFirstName() { return firstName; }
    public String getEmail() { return email; }
}

