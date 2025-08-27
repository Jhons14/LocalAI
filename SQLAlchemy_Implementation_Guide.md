# SQLAlchemy Implementation Guide - LocalAI Project

## Overview

This document explains the SQLAlchemy implementation in the LocalAI project backend. SQLAlchemy is a Python Object-Relational Mapping (ORM) library that provides a high-level interface for interacting with databases using Python objects instead of raw SQL queries.

## Architecture Overview

The SQLAlchemy implementation follows a clean, modular architecture with the following structure:

```
backend/database/
├── __init__.py          # Package exports
├── base.py              # Database engine and base configuration  
├── session.py           # Session management and dependencies
└── models.py            # Database models/tables
```

## Core Components

### 1. Database Base Configuration (`base.py`)

**Purpose**: Sets up the fundamental SQLAlchemy components.

**Key Elements**:
- **Engine Creation**: Creates a connection to the database
- **Session Factory**: Produces database sessions for transactions
- **Declarative Base**: Base class for all database models
- **Naming Convention**: Standardizes database constraint names

**Configuration Features**:
```python
# Engine with configurable settings
engine = create_engine(
    settings.database.url,           # Database connection string
    echo=settings.database.echo,     # SQL logging for debugging
    pool_size=settings.database.pool_size,        # Connection pool size
    max_overflow=settings.database.max_overflow,  # Extra connections allowed
    connect_args={"check_same_thread": False}      # SQLite threading fix
)
```

**Naming Convention**: Ensures consistent constraint naming across databases:
- `ix_`: Index names
- `uq_`: Unique constraint names  
- `fk_`: Foreign key constraint names
- `pk_`: Primary key constraint names
- `ck_`: Check constraint names

### 2. Session Management (`session.py`)

**Purpose**: Handles database session lifecycle and dependency injection.

**Key Functions**:

- **`get_db()`**: FastAPI dependency that provides database sessions
  - Creates a new session for each request
  - Automatically closes sessions after use
  - Handles errors with automatic rollback
  - Used with `Depends(get_db)` in FastAPI endpoints

- **`create_tables()`**: Creates all database tables from models
  - Called during application startup
  - Uses `Base.metadata.create_all()`
  - Includes error handling and logging

- **`drop_tables()`**: Drops all tables (development/testing only)

### 3. Database Models (`models.py`)

**Purpose**: Defines the database schema using Python classes.

#### Base Mixin

**`TimestampMixin`**: Adds automatic timestamp tracking to models
- `created_at`: Automatically set when record is created
- `updated_at`: Automatically updated when record is modified
- Uses `func.now()` for timezone-aware timestamps

#### Model Definitions

**1. User Model**
```python
class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Security features
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
```

**Features**:
- UUID primary keys for security
- Email and username uniqueness constraints
- Account locking mechanism for security
- Automatic timestamp tracking
- Relationships to API keys and chat sessions

**2. APIKey Model**
```python
class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"
    
    user_id = Column(String, ForeignKey("users.id"))
    provider = Column(String(50))  # 'openai', 'ollama', etc.
    model_name = Column(String(100))
    encrypted_key = Column(Text)  # Encrypted storage
    usage_count = Column(Integer, default=0)
```

**Features**:
- Encrypted API key storage
- Provider and model tracking
- Usage statistics
- Composite indexes for performance

**3. ChatSession Model**
```python
class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"
    
    thread_id = Column(String(100), index=True)  # External identifier
    provider = Column(String(50))
    model_name = Column(String(100))
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
```

**Features**:
- Groups related chat messages
- Tracks usage statistics
- Supports anonymous sessions
- Performance indexes

**4. ChatMessage Model**
```python
class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"
    
    role = Column(String(20))      # 'user', 'assistant', 'system'
    content = Column(Text)
    token_count = Column(Integer)
    processing_time_ms = Column(Integer)
    is_error = Column(Boolean, default=False)
```

**Features**:
- Stores individual chat messages
- Performance metrics tracking
- Error state handling
- Content preview property

## Key SQLAlchemy Concepts Used

### 1. Declarative Base
- All models inherit from `Base`
- `Base` is created using `declarative_base()`
- Provides common functionality to all models

### 2. Column Types
- **String**: Text with length limits
- **Text**: Unlimited text storage
- **Integer**: Numeric values
- **Boolean**: True/false values
- **DateTime**: Timestamp with timezone support
- **UUID**: PostgreSQL-specific UUID type

### 3. Relationships
```python
# One-to-many relationship
api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

# Foreign key
user_id = Column(String, ForeignKey("users.id"))
```

**Cascade Options**:
- `"all, delete-orphan"`: When parent is deleted, delete all related records

### 4. Indexes and Performance
```python
# Single column index
email = Column(String(255), unique=True, index=True)

# Composite indexes
__table_args__ = (
    Index("idx_api_keys_user_provider_model", "user_id", "provider", "model_name"),
    Index("idx_chat_sessions_activity", "last_activity"),
)
```

### 5. Properties and Methods
```python
@property
def is_locked(self) -> bool:
    """Custom property to check account lock status"""
    if self.locked_until is None:
        return False
    return datetime.utcnow() < self.locked_until
```

## Integration with FastAPI

### Dependency Injection
```python
@app.post("/users")
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # db session is automatically provided and managed
    new_user = User(**user_data.dict())
    db.add(new_user)
    db.commit()
    return new_user
```

### Error Handling
The `get_db()` function includes automatic error handling:
- Exceptions trigger automatic rollback
- Sessions are always properly closed
- Errors are logged for debugging

## Database Migration Strategy

The project uses a simple migration approach:

1. **Development**: `create_tables()` creates all tables automatically
2. **Manual Migrations**: Located in `migrations/` directory
3. **Schema Changes**: Modify models and create migration scripts

## Security Features

### 1. Input Sanitization
- All user inputs are validated through Pydantic models
- SQL injection prevention through parameterized queries

### 2. Encrypted Storage
- API keys are encrypted before database storage
- Passwords are hashed using secure algorithms

### 3. Account Security
- Failed login attempt tracking
- Account locking mechanism
- Timezone-aware timestamps

## Performance Optimizations

### 1. Connection Pooling
```python
engine = create_engine(
    url,
    pool_size=10,        # Base pool size
    max_overflow=20      # Additional connections when needed
)
```

### 2. Strategic Indexing
- Primary keys on all tables
- Foreign key indexes for joins
- Composite indexes for common query patterns
- Activity-based indexes for sorting

### 3. Session Management
- Sessions are created per request
- Automatic cleanup prevents connection leaks
- Error handling with rollback

## Common Usage Patterns

### 1. Creating Records
```python
async def create_user(db: Session, user_data: dict):
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)  # Get updated data from DB
    return user
```

### 2. Querying Records
```python
# Single record
user = db.query(User).filter(User.email == email).first()

# Multiple records with joins
sessions = db.query(ChatSession)\
    .join(User)\
    .filter(User.id == user_id)\
    .order_by(ChatSession.last_activity.desc())\
    .all()
```

### 3. Updating Records
```python
db.query(User)\
    .filter(User.id == user_id)\
    .update({"last_login": datetime.utcnow()})
db.commit()
```

### 4. Relationships and Joins
```python
# Accessing related data
user_with_sessions = db.query(User)\
    .options(selectinload(User.chat_sessions))\
    .filter(User.id == user_id)\
    .first()
```

## Environment Configuration

Database settings are managed through the configuration system:

```python
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/localai
DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Best Practices Implemented

1. **Separation of Concerns**: Models, sessions, and configuration are separate
2. **Dependency Injection**: Database sessions are injected as needed
3. **Error Handling**: Comprehensive error handling with logging
4. **Security**: Encrypted sensitive data, input validation
5. **Performance**: Connection pooling, strategic indexing
6. **Maintainability**: Clear naming conventions, documentation
7. **Testing**: Separate functions for table creation/destruction

## Testing Support

The implementation supports testing through:
- `drop_tables()` and `create_tables()` functions
- Session isolation
- Test database configuration
- Mock-friendly dependency injection

This SQLAlchemy implementation provides a robust, secure, and scalable foundation for the LocalAI project's data persistence needs.