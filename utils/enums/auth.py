from enum import Enum

class AuthMessage(Enum):
    # Success Messages
    SUCCESS_LOGIN = "Login successful!"
    SUCCESS_REGISTER = "Registration completed successfully!"
    SUCCESS_LOGOUT = "Logout successful!"
    SUCCESS_PROFILE_UPDATE = "Profile updated successfully!"
    SUCCESS_PROFILE_RETRIEVED = "Profile retrieved successfully!"
    SUCCESS_PHONE_VERIFIED = "Phone number verified successfully!"
    SUCCESS_ADMIN_LOGIN = "Admin login successful!"
    SUCCESS_ADMIN_LOGOUT = "Admin logout successful!"
    SUCCESS_ADMIN_PROFILE = "Admin profile retrieved successfully!"
    
    # Registration Errors
    PASSWORD_MISMATCH = "Passwords do not match."
    REGISTRATION_FAILED = "Registration failed. Please check your details."
    PHONE_ALREADY_EXISTS = "Phone number already registered."
    EMAIL_ALREADY_EXISTS = "Email address already registered."
    
    # Login Errors
    ERROR_INVALID_CREDENTIALS = "Invalid phone number or password."
    ERROR_ADMIN_INVALID_CREDENTIALS = "Invalid admin credentials."
    ERROR_USER_NOT_FOUND = "User not found."
    ERROR_UNAUTHORIZED = "You are not authorized to access this resource."
    ERROR_ACCOUNT_LOCKED = "Your account has been locked. Please contact support."
    DISABLED_ACCOUNT = "Your account has been disabled. Please contact support."
    ADMIN_ACCESS_REQUIRED = "Admin access required."
    
    # Credential Errors
    CREDENTIALS_NOT_PROVIDED = "Must include phone number and password."
    ADMIN_CREDENTIALS_NOT_PROVIDED = "Must include username and password."
    
    # Token Errors
    TOKEN_EXPIRED = "Token has expired."
    TOKEN_REQUIRED = "Token is required."
    REFRESH_TOKEN_REQUIRED = "Refresh token is required."
    INVALID_TOKEN = "Invalid token."
    BAD_TOKEN_FORMAT = "Invalid token format."
    
    # Phone Verification
    OTP_SENT = "Verification code sent to your phone."
    INVALID_OTP = "Invalid verification code."
    OTP_EXPIRED = "Verification code has expired."
    PHONE_VERIFICATION_REQUIRED = "Please verify your phone number."
    
    # Profile Errors
    PROFILE_UPDATE_FAILED = "Profile update failed."
    INVALID_PHONE_FORMAT = "Invalid phone number format."
    
    # Client Specific
    CLIENT_NOT_FOUND = "Client not found."
    VERIFICATION_REQUIRED = "Account verification required."

    @property
    def value(self):
        return self._value_