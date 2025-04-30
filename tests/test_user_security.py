import pytest
import pytest_asyncio
import bcrypt
import jwt
from src.business_logic.user_service import UserService
from src.database.models import User

@pytest.mark.asyncio
class TestUserSecurity:
    def test_user_creation(self, user_service, db_session):
        """Test user creation with secure password hashing"""
        user = user_service.create_user(
            username='newuser',
            password='SecurePass123!',
            role='user',
            name='New User'
        )
        assert user is not None
        assert user.username == 'newuser'
        assert user.role == 'user'
        assert bcrypt.checkpw('SecurePass123!'.encode(), user.password_hash.encode())

    def test_password_requirements(self, user_service):
        """Test password requirements enforcement"""
        # Too short
        user1 = user_service.create_user(
            username='test1',
            password='short',  # Less than 8 characters
            role='user',
            name='Test User 1'
        )
        assert user1 is None

        # No numbers
        user2 = user_service.create_user(
            username='test2',
            password='NoNumbers!',
            role='user',
            name='Test User 2'
        )
        assert user2 is None

        # No special characters
        user3 = user_service.create_user(
            username='test3',
            password='NoSpecial123',
            role='user',
            name='Test User 3'
        )
        assert user3 is None

        # Valid password
        user4 = user_service.create_user(
            username='test4',
            password='Valid123!',
            role='user',
            name='Test User 4'
        )
        assert user4 is not None

    @pytest.mark.asyncio
    async def test_authentication(self, user_service, db_session):
        """Test user authentication and JWT token generation"""
        # Create test user first
        test_user = user_service.create_user(
            username='auth_test',
            password='AuthTest123!',
            role='user',
            name='Auth Test User'
        )
        assert test_user is not None
        
        # Test successful authentication
        token = user_service.authenticate('auth_test', 'AuthTest123!')
        assert token is not None

        # Verify token contents
        payload = await user_service.verify_token(token)
        assert payload is not None
        assert payload['username'] == 'auth_test'
        assert payload['role'] == 'user'
        assert 'jti' in payload  # Unique token ID
        assert 'exp' in payload  # Expiration time

    @pytest.mark.asyncio
    async def test_token_expiration(self, user_service, db_session):
        """Test JWT token expiration"""
        # Create test user
        test_user = user_service.create_user(
            username='expiry_test',
            password='Expiry123!',
            role='user',
            name='Expiry Test User'
        )
        assert test_user is not None

        # Generate token
        token = user_service.authenticate('expiry_test', 'Expiry123!')
        assert token is not None

        # Verify token is currently valid
        payload = await user_service.verify_token(token)
        assert payload is not None

        # Force token expiration
        user_service.jwt_expiry = -1  # Set negative expiry to force expiration
        expired_payload = await user_service.verify_token(token)
        assert expired_payload is None

    def test_role_based_access(self, user_service, db_session):
        """Test role-based access control"""
        # Create test users
        user = user_service.create_user(
            username='user_test',
            password='UserTest123!',
            role='user',
            name='User Test'
        )
        
        admin = user_service.create_user(
            username='admin_test',
            password='AdminTest123!',
            role='admin',
            name='Admin Test'
        )

        # Test user permissions
        assert user_service.check_permission(user.id, 'view_devices') is True
        assert user_service.check_permission(user.id, 'manage_users') is False

        # Test admin permissions
        assert user_service.check_permission(admin.id, 'view_devices') is True
        assert user_service.check_permission(admin.id, 'manage_users') is True

    def test_activity_logging(self, user_service, db_session):
        """Test user activity logging"""
        # Create test user
        test_user = user_service.create_user(
            username='log_test',
            password='LogTest123!',
            role='user',
            name='Log Test User'
        )
        assert test_user is not None

        # Log some activities
        user_service.log_activity(test_user.id, 'login')
        user_service.log_activity(test_user.id, 'view_device')
        user_service.log_activity(test_user.id, 'logout')

        # Retrieve logs
        logs = user_service.get_user_activity(test_user.id)
        assert len(logs) == 3
        assert logs[0]['action'] == 'login'
        assert logs[1]['action'] == 'view_device'
        assert logs[2]['action'] == 'logout'

    def test_account_deactivation(self, user_service, db_session):
        """Test user account deactivation"""
        # Create test user
        test_user = user_service.create_user(
            username='deactivate_test',
            password='Deactivate123!',
            role='user',
            name='Deactivate Test User'
        )
        assert test_user is not None

        # Verify initial active status
        assert test_user.is_active is True

        # Deactivate account
        user_service.deactivate_user(test_user.id)
        deactivated_user = user_service.get_user(test_user.id)
        assert deactivated_user.is_active is False

        # Verify authentication fails for deactivated account
        token = user_service.authenticate('deactivate_test', 'Deactivate123!')
        assert token is None

    @pytest.mark.asyncio
    async def test_secret_rotation(self, user_service, db_session):
        """Test JWT secret rotation"""
        # Create test user
        test_user = user_service.create_user(
            username='rotation_test',
            password='Rotation123!',
            role='user',
            name='Rotation Test User'
        )
        assert test_user is not None

        # Generate token with current secret
        token = user_service.authenticate('rotation_test', 'Rotation123!')
        assert token is not None

        # Verify token is valid before rotation
        payload = await user_service.verify_token(token)
        assert payload is not None
        assert payload['username'] == 'rotation_test'

        # Store the old token and secret
        old_token = token
        old_secret = user_service.jwt_secret

        # Generate new token before rotation to compare
        new_token_before = user_service.authenticate('rotation_test', 'Rotation123!')
        assert new_token_before is not None

        # Rotate the secret
        user_service.rotate_jwt_secret()
        assert user_service.jwt_secret != old_secret
        assert user_service.previous_jwt_secret == old_secret

        # Old token should still work during grace period
        old_payload = await user_service.verify_token(old_token)
        assert old_payload is not None
        assert old_payload['username'] == 'rotation_test'

        # New token with new secret
        new_token = user_service.authenticate('rotation_test', 'Rotation123!')
        assert new_token is not None
        assert new_token != old_token

        # Verify new token works
        new_payload = await user_service.verify_token(new_token)
        assert new_payload is not None
        assert new_payload['username'] == 'rotation_test'