"""
Entity Access Classes
Minimal class-based wrappers for specific entities.
Objects are only instantiated when explicitly requested.
All processing is delegated to the database.
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime, date
from dataclasses import dataclass
from .data_access_layer import get_dal
import logging

logger = logging.getLogger(__name__)


# ==================== LAZY-LOADED ENTITY CLASSES ====================
# These classes are minimal wrappers around database records
# They are only instantiated when the GUI explicitly requests complete data


@dataclass
class User:
    """
    Minimal User entity - only instantiated when complete user data is requested.
    """
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    password_hash: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from database dictionary."""
        return cls(
            id=str(data['id']),
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            role=data['role'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            is_active=data['is_active'],
            password_hash=data.get('password_hash')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding password_hash)."""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'is_active': self.is_active
        }


@dataclass
class Tenant:
    """
    Minimal Tenant entity - only instantiated when requested.
    """
    id: str
    user_id: Optional[str]
    unit_id: Optional[str]
    move_in_date: Optional[date]
    move_out_date: Optional[date]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """Create Tenant instance from database dictionary."""
        return cls(
            id=str(data['id']),
            user_id=str(data['user_id']) if data.get('user_id') else None,
            unit_id=str(data['unit_id']) if data.get('unit_id') else None,
            move_in_date=data.get('move_in_date'),
            move_out_date=data.get('move_out_date'),
            created_at=data['created_at'],
            metadata=data.get('metadata')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'unit_id': self.unit_id,
            'move_in_date': self.move_in_date.isoformat() if isinstance(self.move_in_date, date) else self.move_in_date,
            'move_out_date': self.move_out_date.isoformat() if isinstance(self.move_out_date, date) else self.move_out_date,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'metadata': self.metadata
        }


@dataclass
class Unit:
    """
    Minimal Unit entity - only instantiated when requested.
    """
    id: str
    building_id: str
    unit_number: Optional[str]
    floor: Optional[int]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    sqft: Optional[int]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Unit':
        """Create Unit instance from database dictionary."""
        return cls(
            id=str(data['id']),
            building_id=str(data['building_id']),
            unit_number=data.get('unit_number'),
            floor=data.get('floor'),
            bedrooms=data.get('bedrooms'),
            bathrooms=float(data['bathrooms']) if data.get('bathrooms') else None,
            sqft=data.get('sqft'),
            created_at=data['created_at'],
            metadata=data.get('metadata')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'building_id': self.building_id,
            'unit_number': self.unit_number,
            'floor': self.floor,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'sqft': self.sqft,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'metadata': self.metadata
        }


@dataclass
class Booking:
    """
    Minimal Booking entity - only instantiated when requested.
    """
    id: str
    reference: Optional[str]
    tenant_id: Optional[str]
    requestor_user_id: Optional[str]
    unit_id: Optional[str]
    service_type_id: Optional[str]
    status: str
    priority: str
    notes: Optional[str]
    estimated_duration_minutes: Optional[int]
    price_cents: Optional[int]
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    provider_staff_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Booking':
        """Create Booking instance from database dictionary."""
        return cls(
            id=str(data['id']),
            reference=data.get('reference'),
            tenant_id=str(data['tenant_id']) if data.get('tenant_id') else None,
            requestor_user_id=str(data['requestor_user_id']) if data.get('requestor_user_id') else None,
            unit_id=str(data['unit_id']) if data.get('unit_id') else None,
            service_type_id=str(data['service_type_id']) if data.get('service_type_id') else None,
            status=data['status'],
            priority=data.get('priority', 'normal'),
            notes=data.get('notes'),
            estimated_duration_minutes=data.get('estimated_duration_minutes'),
            price_cents=data.get('price_cents'),
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            cancelled_at=data.get('cancelled_at'),
            cancelled_by=str(data['cancelled_by']) if data.get('cancelled_by') else None,
            scheduled_start=data.get('scheduled_start'),
            scheduled_end=data.get('scheduled_end'),
            provider_staff_id=str(data['provider_staff_id']) if data.get('provider_staff_id') else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'reference': self.reference,
            'tenant_id': self.tenant_id,
            'requestor_user_id': self.requestor_user_id,
            'unit_id': self.unit_id,
            'service_type_id': self.service_type_id,
            'status': self.status,
            'priority': self.priority,
            'notes': self.notes,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'price_cents': self.price_cents,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'cancelled_at': self.cancelled_at.isoformat() if isinstance(self.cancelled_at, datetime) else self.cancelled_at,
            'cancelled_by': self.cancelled_by,
            'scheduled_start': self.scheduled_start.isoformat() if isinstance(self.scheduled_start, datetime) else self.scheduled_start,
            'scheduled_end': self.scheduled_end.isoformat() if isinstance(self.scheduled_end, datetime) else self.scheduled_end,
            'provider_staff_id': self.provider_staff_id
        }


# ==================== ENTITY-SPECIFIC ACCESS CLASSES ====================
# These provide entity-specific methods while maintaining lazy instantiation


class UserAccess:
    """
    Access layer for User entities.
    Methods return either simple data (IDs) or dictionaries (not objects by default).
    """
    
    def __init__(self):
        self.dal = get_dal()
        self.table = 'users'
    
    # Simple queries (no object instantiation)
    
    def get_all_user_ids(self) -> List[str]:
        """Get all user IDs."""
        return self.dal.get_all_ids(self.table)
    
    def get_active_user_ids(self) -> List[str]:
        """Get IDs of active users only."""
        return self.dal.get_filtered_ids(self.table, "is_active = true", ())
    
    def get_users_by_role_ids(self, role: str) -> List[str]:
        """Get user IDs filtered by role."""
        return self.dal.get_filtered_ids(self.table, "role = %s", (role,))
    
    def user_exists(self, user_id: Union[str, UUID]) -> bool:
        """Check if user exists."""
        return self.dal.record_exists(self.table, user_id)
    
    def count_users_by_role(self, role: str) -> int:
        """Count users by role."""
        return self.dal.count_records(self.table, "role = %s", (role,))
    
    # Complete data queries (returns dictionaries, not objects)
    
    def get_user_data(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get complete user data as dictionary."""
        return self.dal.get_record_by_id(self.table, user_id)
    
    def get_user(self, user_id: Union[str, UUID]) -> Optional[User]:
        """
        Get user as instantiated object.
        Only use when the GUI explicitly needs an object.
        """
        data = self.get_user_data(user_id)
        return User.from_dict(data) if data else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email as dictionary."""
        results = self.dal.get_filtered_records(self.table, "email = %s", (email,), limit=1)
        return results[0] if results else None
    
    def get_all_users_data(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users as dictionaries."""
        if active_only:
            return self.dal.get_filtered_records(self.table, "is_active = true", ())
        return self.dal.get_filtered_records(self.table, "1=1", ())
    
    # Modification operations
    
    def create_user(self, email: str, full_name: str, role: str, 
                   phone: str = None, password_hash: str = None) -> str:
        """Create new user and return ID."""
        data = {
            'email': email,
            'full_name': full_name,
            'role': role,
            'phone': phone,
            'password_hash': password_hash,
            'is_active': True
        }
        return self.dal.insert_record(self.table, data)
    
    def update_user(self, user_id: Union[str, UUID], **kwargs) -> bool:
        """Update user fields."""
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        return self.dal.update_record(self.table, user_id, kwargs)
    
    def deactivate_user(self, user_id: Union[str, UUID]) -> bool:
        """Deactivate user."""
        return self.update_user(user_id, is_active=False)


class TenantAccess:
    """
    Access layer for Tenant entities.
    """
    
    def __init__(self):
        self.dal = get_dal()
        self.table = 'tenants'
    
    def get_all_tenant_ids(self) -> List[str]:
        """Get all tenant IDs."""
        return self.dal.get_all_ids(self.table)
    
    def get_current_tenant_ids(self) -> List[str]:
        """Get IDs of current tenants (those without move_out_date)."""
        return self.dal.get_filtered_ids(
            self.table, 
            "move_out_date IS NULL OR move_out_date > CURRENT_DATE", 
            ()
        )
    
    def get_tenants_by_unit_ids(self, unit_id: Union[str, UUID]) -> List[str]:
        """Get tenant IDs for a specific unit."""
        return self.dal.get_filtered_ids(self.table, "unit_id = %s", (str(unit_id),))
    
    def get_tenant_data(self, tenant_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get complete tenant data as dictionary."""
        return self.dal.get_record_by_id(self.table, tenant_id)
    
    def get_tenant(self, tenant_id: Union[str, UUID]) -> Optional[Tenant]:
        """Get tenant as instantiated object."""
        data = self.get_tenant_data(tenant_id)
        return Tenant.from_dict(data) if data else None
    
    def get_tenant_with_user_info(self, tenant_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get tenant with joined user information.
        Demonstrates database-side JOIN processing.
        """
        query = """
            SELECT t.*, u.email, u.full_name, u.phone
            FROM tenants t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.id = %s
        """
        return self.dal.execute_custom_query(query, (str(tenant_id),), fetch='one')
    
    def create_tenant(self, user_id: str, unit_id: str = None, 
                     move_in_date: date = None, **kwargs) -> str:
        """Create new tenant and return ID."""
        data = {
            'user_id': user_id,
            'unit_id': unit_id,
            'move_in_date': move_in_date,
            **kwargs
        }
        return self.dal.insert_record(self.table, data)
    
    def update_tenant(self, tenant_id: Union[str, UUID], **kwargs) -> bool:
        """Update tenant fields."""
        return self.dal.update_record(self.table, tenant_id, kwargs)


class UnitAccess:
    """
    Access layer for Unit entities.
    """
    
    def __init__(self):
        self.dal = get_dal()
        self.table = 'units'
    
    def get_all_unit_ids(self) -> List[str]:
        """Get all unit IDs."""
        return self.dal.get_all_ids(self.table)
    
    def get_units_by_building_ids(self, building_id: Union[str, UUID]) -> List[str]:
        """Get unit IDs for a specific building."""
        return self.dal.get_filtered_ids(self.table, "building_id = %s", (str(building_id),))
    
    def get_vacant_unit_ids(self) -> List[str]:
        """
        Get IDs of vacant units (no current tenants).
        Uses database-side subquery.
        """
        query = """
            SELECT id FROM units
            WHERE id NOT IN (
                SELECT DISTINCT unit_id FROM tenants
                WHERE unit_id IS NOT NULL
                AND (move_out_date IS NULL OR move_out_date > CURRENT_DATE)
            )
            ORDER BY created_at DESC
        """
        results = self.dal.execute_custom_query(query, fetch='all')
        return [str(row['id']) for row in results] if results else []
    
    def get_unit_data(self, unit_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get complete unit data as dictionary."""
        return self.dal.get_record_by_id(self.table, unit_id)
    
    def get_unit(self, unit_id: Union[str, UUID]) -> Optional[Unit]:
        """Get unit as instantiated object."""
        data = self.get_unit_data(unit_id)
        return Unit.from_dict(data) if data else None
    
    def create_unit(self, building_id: str, unit_number: str = None, **kwargs) -> str:
        """Create new unit and return ID."""
        data = {
            'building_id': building_id,
            'unit_number': unit_number,
            **kwargs
        }
        return self.dal.insert_record(self.table, data)


class BookingAccess:
    """
    Access layer for Booking entities.
    """
    
    def __init__(self):
        self.dal = get_dal()
        self.table = 'bookings'
    
    def get_all_booking_ids(self) -> List[str]:
        """Get all booking IDs."""
        return self.dal.get_all_ids(self.table)
    
    def get_bookings_by_status_ids(self, status: str) -> List[str]:
        """Get booking IDs by status."""
        return self.dal.get_filtered_ids(self.table, "status = %s", (status,))
    
    def get_bookings_by_tenant_ids(self, tenant_id: Union[str, UUID]) -> List[str]:
        """Get booking IDs for a specific tenant."""
        return self.dal.get_filtered_ids(self.table, "tenant_id = %s", (str(tenant_id),))
    
    def get_bookings_by_unit_ids(self, unit_id: Union[str, UUID]) -> List[str]:
        """Get booking IDs for a specific unit."""
        return self.dal.get_filtered_ids(self.table, "unit_id = %s", (str(unit_id),))
    
    def get_booking_data(self, booking_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get complete booking data as dictionary."""
        return self.dal.get_record_by_id(self.table, booking_id)
    
    def get_booking(self, booking_id: Union[str, UUID]) -> Optional[Booking]:
        """Get booking as instantiated object."""
        data = self.get_booking_data(booking_id)
        return Booking.from_dict(data) if data else None
    
    def get_booking_with_details(self, booking_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get booking with all related information (tenant, unit, service type).
        Demonstrates complex JOIN processing in database.
        """
        query = """
            SELECT 
                b.*,
                t.id as tenant_id, u.full_name as tenant_name, u.email as tenant_email,
                un.unit_number, un.building_id,
                st.name as service_type_name, st.code as service_type_code,
                a.provider_id, a.provider_staff_id, a.status as assignment_status
            FROM bookings b
            LEFT JOIN tenants t ON b.tenant_id = t.id
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN units un ON b.unit_id = un.id
            LEFT JOIN service_types st ON b.service_type_id = st.id
            LEFT JOIN assignments a ON b.id = a.booking_id
            WHERE b.id = %s
        """
        return self.dal.execute_custom_query(query, (str(booking_id),), fetch='one')
    
    def create_booking(self, unit_id: str, service_type_id: str, 
                      tenant_id: str = None, requestor_user_id: str = None,
                      **kwargs) -> str:
        """Create new booking and return ID."""
        data = {
            'unit_id': unit_id,
            'service_type_id': service_type_id,
            'tenant_id': tenant_id,
            'requestor_user_id': requestor_user_id,
            'status': kwargs.get('status', 'requested'),
            'priority': kwargs.get('priority', 'normal'),
            **{k: v for k, v in kwargs.items() if k not in ['status', 'priority']}
        }
        return self.dal.insert_record(self.table, data)
    
    def update_booking(self, booking_id: Union[str, UUID], **kwargs) -> bool:
        """Update booking fields."""
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        return self.dal.update_record(self.table, booking_id, kwargs)
    
    def update_booking_status(self, booking_id: Union[str, UUID], new_status: str) -> bool:
        """Update booking status."""
        return self.update_booking(booking_id, status=new_status)


# ==================== FACTORY FUNCTIONS ====================
# Provide easy access to entity-specific classes


def get_user_access() -> UserAccess:
    """Get UserAccess instance."""
    return UserAccess()


def get_tenant_access() -> TenantAccess:
    """Get TenantAccess instance."""
    return TenantAccess()


def get_unit_access() -> UnitAccess:
    """Get UnitAccess instance."""
    return UnitAccess()


def get_booking_access() -> BookingAccess:
    """Get BookingAccess instance."""
    return BookingAccess()
