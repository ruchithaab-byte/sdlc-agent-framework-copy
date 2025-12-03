# Auth System & Dashboard Components Review

## Issues Found

### 1. **Deprecated datetime.utcnow() Usage**
**Files:**
- `src/auth/auth_utils.py` (line 77)
- `src/auth/auth_api.py` (lines 74, 149)
- `src/logging/execution_logger.py` (multiple lines)

**Issue:** `datetime.utcnow()` is deprecated in Python 3.12+
**Fix:** Use `datetime.now(timezone.utc)` instead

### 2. **Incorrect expires_at Calculation**
**File:** `src/auth/auth_api.py` (line 150)
**Issue:** `now.replace(hour=now.hour + 24)` is incorrect - doesn't handle day rollover
**Fix:** Use `now + timedelta(hours=24)`

### 3. **Missing JWT_SECRET Validation**
**Files:** `src/auth/auth_api.py`, `main.py`
**Issue:** No check if JWT_SECRET is set before generating tokens
**Fix:** Add validation in login/create_user functions

### 4. **WebSocket Handler Path Extraction**
**File:** `src/dashboard/websocket_server.py` (line 80)
**Issue:** Path extraction from query string might not work correctly with websockets library
**Fix:** Use proper websockets path handling

### 5. **Missing Error Handling**
**Files:** Multiple
**Issue:** Database connection errors, missing tables not handled gracefully
**Fix:** Add try-catch blocks and better error messages

### 6. **Token Revocation Check Performance**
**File:** `src/auth/middleware.py` (line 58-72)
**Issue:** Database query on every request - could be slow
**Note:** Acceptable for now, but could cache or optimize later

### 7. **CORS Middleware Order**
**File:** `src/dashboard/websocket_server.py` (line 117)
**Issue:** CORS middleware should be added before routes
**Fix:** Move middleware setup before route registration

### 8. **Missing Route for All Deployments**
**File:** `src/dashboard/summary_api.py`
**Issue:** `/api/summary/deployments/{repo_id}` requires repo_id, no route for all deployments
**Fix:** Add optional repo_id or separate route

## Recommendations

1. **Add request logging** for debugging
2. **Add rate limiting** for auth endpoints
3. **Add token refresh** mechanism
4. **Add password reset** functionality
5. **Add user management** endpoints (list, update, delete)
6. **Add health check** endpoint

