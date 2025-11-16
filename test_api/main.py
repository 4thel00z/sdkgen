"""Comprehensive FastAPI test app for SDK generator validation."""

from enum import Enum
from typing import Literal

from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import Query
from fastapi import UploadFile
from pydantic import BaseModel


app = FastAPI(
    title="Comprehensive Test API",
    version="1.0.0",
    description="API with all edge cases for testing SDK generation",
)


# ============================================================================
# Enums
# ============================================================================


class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class FileType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    VIDEO = "video"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    CRYPTO = "crypto"


# ============================================================================
# Models - V1
# ============================================================================


class User(BaseModel):
    id: str
    name: str
    email: str
    age: int | None = None
    role: UserRole = UserRole.USER
    tags: list[str] = []
    metadata: dict[str, str] = {}
    is_active: bool = True


class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int | None = None
    role: UserRole = UserRole.USER
    tags: list[str] = []
    metadata: dict[str, str] = {}


class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class PaginatedUsers(BaseModel):
    users: list[User]
    page: int
    size: int
    total: int


class Product(BaseModel):
    id: str
    name: str
    price: float
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    in_stock: bool
    quantity: int = 0
    categories: list[str] = []
    metadata: dict[str, str | int | bool] = {}


class CreateProductRequest(BaseModel):
    name: str
    price: float
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    in_stock: bool = True
    quantity: int = 0
    categories: list[str] = []


class Order(BaseModel):
    id: str
    user_id: str
    product_ids: list[str]
    total_amount: float
    currency: str = "USD"
    status: OrderStatus
    payment_method: PaymentMethod
    shipping_address: dict[str, str]
    created_at: str
    updated_at: str


class CreateOrderRequest(BaseModel):
    user_id: str
    product_ids: list[str]
    payment_method: PaymentMethod
    shipping_address: dict[str, str]


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    file_type: FileType
    url: str


class DocumentMetadata(BaseModel):
    title: str
    author: str | None = None
    created_at: str
    tags: list[str] = []


class Document(BaseModel):
    id: str
    content: str
    metadata: DocumentMetadata
    version: int = 1


# ============================================================================
# Models - V2 (with breaking changes)
# ============================================================================


class UserV2(BaseModel):
    """V2 user with additional fields."""

    id: str
    username: str  # Changed from 'name'
    email: str
    age: int | None = None
    role: UserRole = UserRole.USER
    tags: list[str] = []
    metadata: dict[str, str] = {}
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class CreateUserRequestV2(BaseModel):
    username: str
    email: str
    password: str  # New required field
    age: int | None = None
    role: UserRole = UserRole.USER


# ============================================================================
# Models - Beta (experimental features)
# ============================================================================


class AIModel(BaseModel):
    id: str
    name: str
    provider: Literal["openai", "anthropic", "google"]
    capabilities: list[str]
    max_tokens: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    model_id: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    id: str
    model: str
    response: str
    tokens_used: int


# ============================================================================
# API V1 Endpoints - Users
# ============================================================================


@app.get("/api/v1/users", response_model=PaginatedUsers, tags=["users"])
async def list_users_v1(
    page: int = 0,
    size: int = 100,
    role: UserRole | None = None,
    tags: list[str] = Query(default=[]),
    is_active: bool | None = None,
    name_contains: str | None = None,
):
    """List all users with advanced filtering and pagination."""
    return PaginatedUsers(
        users=[
            User(
                id="1",
                name="Alice",
                email="alice@example.com",
                age=30,
                role=UserRole.ADMIN,
                is_active=True,
            ),
            User(id="2", name="Bob", email="bob@example.com", role=UserRole.USER),
        ],
        page=page,
        size=size,
        total=2,
    )


@app.post("/api/v1/users", response_model=User, status_code=201, tags=["users"])
async def create_user_v1(user: CreateUserRequest):
    """Create a new user."""
    return User(
        id="new-user-123",
        name=user.name,
        email=user.email,
        age=user.age,
        role=user.role,
        tags=user.tags,
        metadata=user.metadata,
    )


@app.get("/api/v1/users/{user_id}", response_model=User, tags=["users"])
async def get_user_v1(
    user_id: str,
    expand: list[str] = Query(default=[]),
    include_metadata: bool = False,
):
    """Get a user by ID with optional expansion."""
    return User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        role=UserRole.USER,
        metadata={"key": "value"} if include_metadata else {},
    )


@app.patch("/api/v1/users/{user_id}", response_model=User, tags=["users"])
async def update_user_v1(user_id: str, update: UpdateUserRequest):
    """Partially update a user."""
    return User(
        id=user_id,
        name=update.name or "Updated",
        email=update.email or "updated@example.com",
        age=update.age,
        role=update.role or UserRole.USER,
    )


@app.delete("/api/v1/users/{user_id}", status_code=204, tags=["users"])
async def delete_user_v1(user_id: str):
    """Delete a user by ID."""
    return None


# ============================================================================
# API V1 Endpoints - Products
# ============================================================================


@app.get("/api/v1/products", response_model=list[Product], tags=["products"])
async def list_products_v1(
    page: int = 0,
    size: int = 100,
    in_stock: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    categories: list[str] = Query(default=[]),
    currency: Literal["USD", "EUR", "GBP"] | None = None,
):
    """List products with advanced filtering."""
    return [
        Product(
            id="1",
            name="Premium Widget",
            price=19.99,
            in_stock=True,
            quantity=100,
            categories=["electronics", "gadgets"],
        ),
        Product(id="2", name="Super Gadget", price=29.99, in_stock=False, quantity=0),
    ]


@app.post("/api/v1/products", response_model=Product, status_code=201, tags=["products"])
async def create_product_v1(product: CreateProductRequest):
    """Create a new product."""
    return Product(
        id="prod-new-123",
        name=product.name,
        price=product.price,
        currency=product.currency,
        in_stock=product.in_stock,
        quantity=product.quantity,
        categories=product.categories,
    )


@app.get("/api/v1/products/{product_id}", response_model=Product, tags=["products"])
async def get_product_v1(product_id: str, expand: list[str] = Query(default=[])):
    """Get product details."""
    return Product(
        id=product_id,
        name="Test Product",
        price=99.99,
        in_stock=True,
        quantity=50,
    )


# ============================================================================
# API V1 Endpoints - Orders
# ============================================================================


@app.get("/api/v1/orders", response_model=list[Order], tags=["orders"])
async def list_orders_v1(
    user_id: str | None = None,
    status: OrderStatus | None = None,
    payment_method: PaymentMethod | None = None,
    min_amount: float | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
):
    """List orders with filtering."""
    return [
        Order(
            id="order-1",
            user_id="user-1",
            product_ids=["prod-1", "prod-2"],
            total_amount=149.99,
            status=OrderStatus.SHIPPED,
            payment_method=PaymentMethod.CREDIT_CARD,
            shipping_address={"street": "123 Main St", "city": "NYC"},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-02T00:00:00Z",
        )
    ]


@app.post("/api/v1/orders", response_model=Order, status_code=201, tags=["orders"])
async def create_order_v1(order: CreateOrderRequest):
    """Create a new order."""
    return Order(
        id="order-new-123",
        user_id=order.user_id,
        product_ids=order.product_ids,
        total_amount=199.99,
        status=OrderStatus.PENDING,
        payment_method=order.payment_method,
        shipping_address=order.shipping_address,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


@app.get("/api/v1/orders/{order_id}", response_model=Order, tags=["orders"])
async def get_order_v1(order_id: str):
    """Get order details."""
    return Order(
        id=order_id,
        user_id="user-1",
        product_ids=["prod-1"],
        total_amount=99.99,
        status=OrderStatus.DELIVERED,
        payment_method=PaymentMethod.CREDIT_CARD,
        shipping_address={"street": "123 Main St"},
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )


# ============================================================================
# API V1 Endpoints - Files (Multipart Upload)
# ============================================================================


@app.post("/api/v1/files", response_model=FileUploadResponse, tags=["files"])
async def upload_file_v1(
    file: UploadFile = File(...),
    file_type: FileType = Form(FileType.DOCUMENT),
    description: str | None = Form(None),
    tags: list[str] = Form(default=[]),
    public: bool = Form(False),
):
    """Upload a file with multipart/form-data."""
    content = await file.read()
    return FileUploadResponse(
        file_id="file-123",
        filename=file.filename or "unknown",
        size=len(content),
        file_type=file_type,
        url=f"https://cdn.example.com/files/file-123",
    )


@app.get("/api/v1/files/{file_id}", response_model=FileUploadResponse, tags=["files"])
async def get_file_v1(file_id: str):
    """Get file metadata."""
    return FileUploadResponse(
        file_id=file_id,
        filename="test.pdf",
        size=1024,
        file_type=FileType.PDF,
        url=f"https://cdn.example.com/files/{file_id}",
    )


@app.get("/api/v1/files/{file_id}/download", tags=["files"])
async def download_file_v1(file_id: str):
    """Download file content as binary."""
    return b"fake file content"


# ============================================================================
# API V1 Endpoints - Documents
# ============================================================================


@app.post("/api/v1/documents", response_model=Document, tags=["documents"])
async def create_document_v1(
    content: str = Form(...),
    title: str = Form(...),
    author: str | None = Form(None),
    tags: list[str] = Form(default=[]),
):
    """Create a document."""
    return Document(
        id="doc-123",
        content=content,
        metadata=DocumentMetadata(
            title=title,
            author=author,
            created_at="2024-01-01T00:00:00Z",
            tags=tags,
        ),
        version=1,
    )


@app.get("/api/v1/documents/{document_id}", response_model=Document, tags=["documents"])
async def get_document_v1(document_id: str, version: int | None = None):
    """Get document by ID and optional version."""
    return Document(
        id=document_id,
        content="Document content here...",
        metadata=DocumentMetadata(
            title="Test Document", created_at="2024-01-01T00:00:00Z"
        ),
        version=version or 1,
    )


# ============================================================================
# API V2 Endpoints - Users (Breaking changes)
# ============================================================================


@app.get("/api/v2/users", response_model=list[UserV2], tags=["users-v2"])
async def list_users_v2(
    page: int = 0,
    size: int = 50,  # Different default
    role: UserRole | None = None,
    is_active: bool = True,
    sort_by: Literal["created_at", "username", "email"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
):
    """List users in V2 API with different defaults and sorting."""
    return [
        UserV2(
            id="1",
            username="alice123",
            email="alice@example.com",
            age=30,
            role=UserRole.ADMIN,
            created_at="2024-01-01T00:00:00Z",
        )
    ]


@app.post("/api/v2/users", response_model=UserV2, status_code=201, tags=["users-v2"])
async def create_user_v2(user: CreateUserRequestV2):
    """Create user in V2 (requires password)."""
    return UserV2(
        id="user-v2-123",
        username=user.username,
        email=user.email,
        age=user.age,
        role=user.role,
        created_at="2024-01-01T00:00:00Z",
    )


@app.get("/api/v2/users/{user_id}", response_model=UserV2, tags=["users-v2"])
async def get_user_v2(user_id: str):
    """Get user in V2 format."""
    return UserV2(
        id=user_id,
        username="testuser",
        email="test@example.com",
        role=UserRole.USER,
        created_at="2024-01-01T00:00:00Z",
    )


# ============================================================================
# API Beta Endpoints - AI/ML Features
# ============================================================================


@app.get("/api/beta/models", response_model=list[AIModel], tags=["ai-beta"])
async def list_ai_models_beta(
    provider: Literal["openai", "anthropic", "google"] | None = None,
    capability: str | None = None,
):
    """List available AI models."""
    return [
        AIModel(
            id="model-1",
            name="GPT-4",
            provider="openai",
            capabilities=["chat", "completion", "embedding"],
            max_tokens=8192,
        ),
        AIModel(
            id="model-2",
            name="Claude-3",
            provider="anthropic",
            capabilities=["chat", "completion"],
            max_tokens=100000,
        ),
    ]


@app.post("/api/beta/chat", response_model=ChatResponse, tags=["ai-beta"])
async def chat_completion_beta(request: ChatRequest):
    """Generate chat completion."""
    return ChatResponse(
        id="chat-123",
        model=request.model_id,
        response="This is a test response",
        tokens_used=150,
    )


@app.post("/api/beta/embeddings", tags=["ai-beta"])
async def create_embeddings_beta(
    texts: list[str],
    model_id: str,
    dimensions: int | None = None,
):
    """Generate embeddings for texts."""
    return {
        "embeddings": [[0.1, 0.2, 0.3] for _ in texts],
        "model": model_id,
        "dimensions": dimensions or 768,
    }


# ============================================================================
# API Beta Endpoints - Search
# ============================================================================


@app.post("/api/beta/search", tags=["search-beta"])
async def search_beta(
    query: str,
    filters: dict[str, str | int | bool] | None = None,
    limit: int = 10,
    offset: int = 0,
    include_facets: bool = False,
):
    """Advanced search with facets."""
    return {
        "results": [
            {"id": "1", "title": "Result 1", "score": 0.95},
            {"id": "2", "title": "Result 2", "score": 0.87},
        ],
        "total": 2,
        "facets": {"category": {"electronics": 10, "books": 5}} if include_facets else None,
    }


# ============================================================================
# API V1 Endpoints - Analytics (Complex responses)
# ============================================================================


@app.get("/api/v1/analytics/summary", tags=["analytics"])
async def get_analytics_summary(
    start_date: str,
    end_date: str,
    metrics: list[str] = Query(default=["revenue", "orders"]),
    group_by: Literal["day", "week", "month"] = "day",
):
    """Get analytics summary with complex nested response."""
    return {
        "period": {"start": start_date, "end": end_date},
        "metrics": {
            "revenue": {"total": 10000.0, "average": 100.0, "currency": "USD"},
            "orders": {"total": 100, "completed": 95, "cancelled": 5},
        },
        "breakdown": [
            {"date": "2024-01-01", "revenue": 1000.0, "orders": 10},
            {"date": "2024-01-02", "revenue": 1200.0, "orders": 12},
        ],
        "comparison": {
            "previous_period": {"revenue": 9000.0, "orders": 90},
            "growth_rate": 0.11,
        },
    }


# ============================================================================
# API V1 Endpoints - Webhooks
# ============================================================================


@app.post("/api/v1/webhooks", tags=["webhooks"])
async def create_webhook_v1(
    url: str,
    events: list[str],
    secret: str | None = None,
    active: bool = True,
    metadata: dict[str, str] = {},
):
    """Register a webhook."""
    return {
        "id": "webhook-123",
        "url": url,
        "events": events,
        "active": active,
        "secret": secret or "generated-secret",
        "created_at": "2024-01-01T00:00:00Z",
    }


@app.get("/api/v1/webhooks", tags=["webhooks"])
async def list_webhooks_v1(active: bool | None = None):
    """List all webhooks."""
    return [
        {
            "id": "webhook-1",
            "url": "https://example.com/webhook",
            "events": ["user.created", "user.updated"],
            "active": True,
        }
    ]


# ============================================================================
# API V1 Endpoints - Batch Operations
# ============================================================================


@app.post("/api/v1/batch/users", tags=["batch"])
async def batch_create_users_v1(users: list[CreateUserRequest]):
    """Batch create users."""
    return {
        "created": len(users),
        "ids": [f"user-{i}" for i in range(len(users))],
    }


@app.delete("/api/v1/batch/users", status_code=200, tags=["batch"])
async def batch_delete_users_v1(user_ids: list[str]):
    """Batch delete users."""
    return {"deleted": len(user_ids)}


# ============================================================================
# Headers and special cases
# ============================================================================


@app.get("/api/v1/auth/me", response_model=User, tags=["auth"])
async def get_current_user_v1(authorization: str = Header(...)):
    """Get current user from auth header."""
    return User(
        id="current-user",
        name="Current User",
        email="current@example.com",
        role=UserRole.USER,
    )


# ============================================================================
# Health and Status
# ============================================================================


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/v1/status", tags=["system"])
async def api_status_v1():
    """API status with metrics."""
    return {
        "status": "operational",
        "uptime": 99.99,
        "requests_per_second": 1000,
        "active_connections": 50,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
