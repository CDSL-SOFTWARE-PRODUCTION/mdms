import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from src.device_communication.base_device import DeviceStatus, ConnectionType
from src.device_communication.secure_device_connection import SecureDeviceCommunication
from src.device_communication.heating_bed import HeatingBed
from src.device_communication.phototherapy_light import PhototherapyLight
from src.device_communication.sterilizer import Sterilizer
from src.device_communication.surgical_light import SurgicalLight

@pytest.mark.asyncio
class TestDeviceCommunication:
    @pytest_asyncio.fixture
    async def secure_comm(self):
        """Setup secure communication instance"""
        comm = SecureDeviceCommunication()
        await comm.initialize()
        return comm

    @pytest_asyncio.fixture
    async def heating_bed(self):
        """Create test heating bed device"""
        device = HeatingBed('TEST-HB-001', 'Test Room')
        await device.initialize()
        return device

    @pytest_asyncio.fixture
    async def phototherapy(self):
        """Create test phototherapy device"""
        device = PhototherapyLight('TEST-PT-001', 'Test Room')
        await device.initialize()
        return device

    @pytest_asyncio.fixture
    async def sterilizer(self):
        """Create test sterilizer device"""
        device = Sterilizer('TEST-ST-001', 'Test Room')
        await device.initialize()
        return device

    async def test_secure_connection(self, secure_comm):
        """Test secure connection establishment"""
        assert secure_comm is not None
        # We expect connection to fail since there's no server running
        try:
            writer = await secure_comm.connect_secure_tcp('localhost', 8000)
            assert writer is None  # Connection should fail
        except ConnectionRefusedError:
            pass  # This is expected

    async def test_encryption_key_rotation(self, secure_comm):
        """Test encryption key rotation"""
        old_key = secure_comm.encryption_key
        assert old_key is not None
        await secure_comm.rotate_encryption_key()
        assert secure_comm.encryption_key != old_key

    async def test_heating_bed_monitoring(self, heating_bed):
        """Test heating bed monitoring and safety features"""
        connected = await heating_bed.connect()
        assert connected is True

        # Test temperature monitoring
        temp = await heating_bed.get_temperature()
        assert 20.0 <= temp <= 40.0

        # Test safety limits
        with pytest.raises(ValueError):
            await heating_bed.set_temperature(45.0)  # Above safe limit

    async def test_phototherapy_session(self, phototherapy):
        """Test phototherapy session management"""
        connected = await phototherapy.connect()
        assert connected is True

        # Test session setup
        session_id = await phototherapy.start_session(
            duration=30,
            intensity=75
        )
        assert session_id is not None

        # Verify session parameters
        session = await phototherapy.get_session(session_id)
        assert session['duration'] == 30
        assert session['intensity'] == 75

    async def test_sterilizer_cycle(self, sterilizer):
        """Test sterilizer cycle management"""
        connected = await sterilizer.connect()
        assert connected is True

        # Start sterilization cycle
        cycle_id = await sterilizer.start_cycle(
            temperature=134,
            duration=20,
            cycle_type='standard'
        )
        assert cycle_id is not None

        # Check cycle status
        status = await sterilizer.get_cycle_status(cycle_id)
        assert status in ['running', 'complete', 'error']

    async def test_device_diagnostics(self, heating_bed, phototherapy, sterilizer):
        """Test device diagnostic capabilities"""
        # Test heating bed diagnostics
        hb_diag = await heating_bed.run_diagnostic()
        assert hb_diag['status'] in ['pass', 'fail', 'warning']

        # Test phototherapy diagnostics
        pt_diag = await phototherapy.run_diagnostic()
        assert pt_diag['status'] in ['pass', 'fail', 'warning']

        # Test sterilizer diagnostics
        st_diag = await sterilizer.run_diagnostic()
        assert st_diag['status'] in ['pass', 'fail', 'warning']

    async def test_error_handling(self, heating_bed):
        """Test error handling and recovery"""
        # Simulate error condition
        heating_bed.status = DeviceStatus.ERROR
        assert heating_bed.status == DeviceStatus.ERROR

        # Test error recovery
        await heating_bed.reset()
        assert heating_bed.status == DeviceStatus.IDLE