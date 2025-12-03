package com.example.app.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {
    private final UserRepository userRepository;
    
    public UserServiceImpl(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    @Override
    @Transactional
    public UserRecord saveNewUser(UserCreationRequestDTO dto) {
        if (userRepository.existsByEmail(dto.email())) {
            throw new BusinessConflictException("Email already in use");
        }
        UserEntity entity = new UserEntity(dto.firstName(), dto.email());
        entity = userRepository.save(entity);
        return new UserRecord(entity.getId(), entity.getFirstName(), entity.getEmail());
    }
    
    @Override
    public UserRecord findById(Long id) {
        UserEntity entity = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User not found: " + id));
        return new UserRecord(entity.getId(), entity.getFirstName(), entity.getEmail());
    }
}

