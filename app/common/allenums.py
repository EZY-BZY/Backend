"""Central place for enums shared across the app."""

from enum import Enum


class ResponseEnum(str, Enum):
    """Common API response messages."""

    SUCCESS = "Success"
    FAIL = "Fail"
    ERROR = "Error"


class AccountType(str, Enum):
    """Beasy employee account type."""

    SUPER_USER = "super_user"
    ADMIN = "admin"
    MEMBER = "member"


class AccountStatus(str, Enum):
    """Beasy employee account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class OwnerAccountStatus(str, Enum):
    """Company owner account status."""

    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    DELETED = "deleted"


class ClientAccountType(str, Enum):
    """Client login account type selector."""

    OWNER = "owner"
    EMPLOYEE = "employee"
    COMPANY_EMPLOYEE = "company_employee"


class CompanyStatus(str, Enum):
    """Company account visibility / lifecycle for client apps."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class CompanyServiceType(str, Enum):
    """What the company offers on the platform."""

    SERVICES = "services"
    PRODUCTS = "products"
    PRODUCTS_AND_SERVICES = "products_and_services"


class BankWalletType(str, Enum):
    """Bank / wallet / app catalog entry type."""

    BANK = "bank"
    WALLET = "wallet"
    APP = "app"


class FixedAssetType(str, Enum):
    """Fixed asset category for a company."""

    CARS_AND_TRUCKS = "cars_and_trucks"
    BUILDING_AND_REAL_ESTATE = "building_and_real_estate"
    MACHINES = "machines"
    COMPUTERS = "computers"
    OFFICE_FURNITURE = "office_furniture"
    OTHER = "other"


class CompanyDocumentType(str, Enum):
    """Company document / file category."""

    DOCUMENT = "document"
    COMMERCIAL_REGISTRATION = "commercial_registration"
    TAX_CARD = "tax_card"
    OPERATION_LICENSE = "operation_license"
    LEASE_CONTRACT = "lease_contract"
    INDUSTRIAL_REGISTRATION = "industrial_registration"
    CONTRACT = "contract"
    OTHER = "other"


class DocumentMediaKind(str, Enum):
    """Kind of attached media for a company document row."""

    IMAGES = "images"
    VIDEOS = "videos"
    FILES = "files"


class CompanyBranchType(str, Enum):
    """Physical site kind for a company branch."""

    FACTORY = "factory"
    WAREHOUSE = "warehouse"
    SHOWROOM = "showroom"
    OFFICE = "office"


class CompanySalarySystem(str, Enum):
    """How salary is quoted for a company employee."""

    MONTHLY = "monthly"
    WEEKLY = "weekly"
    YEARLY = "yearly"
    DAILY = "daily"


class CompanyEmployeeRole(str, Enum):
    """Role of an employee within their company (access / responsibilities)."""

    ADMIN = "admin"
    EMPLOYEE = "employee"
    INVENTORY_MANAGER = "inventory_manager"
    FINANCE = "finance"


class CompanyAuditActorType(str, Enum):
    """Who performed an audited action for company-scoped entities."""

    COMPANY_OWNER = "company_owner"
    EMPLOYEE = "employee"


class Weekday(str, Enum):
    """Day of week for branch working hours (calendar names)."""

    SATURDAY = "saturday"
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"


class CompanyContactChannel(str, Enum):
    """How to interpret ``value`` for a company contact row (JSON key ``type``)."""

    NUMBER = "number"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    THREADS = "threads"
    WHATSAPP = "whatsapp"
    TWITTER_X = "twitter_x"

