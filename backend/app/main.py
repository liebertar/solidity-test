"""
Main FastAPI Application

Enterprise-grade art platform API with blockchain integration.
Follows Hexagonal Architecture with proper dependency injection.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog

from app.config import settings, get_settings
from app.adapters.web3.web3_client_impl import Web3ClientImpl
from app.core.ports.web3_client import NetworkType

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
BLOCKCHAIN_OPERATIONS = Counter('blockchain_operations_total', 'Total blockchain operations', ['operation', 'status'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks"""
    
    # Startup
    logger.info("🚀 Starting Art Platform API", version=settings.APP_VERSION, environment=settings.ENVIRONMENT)
    
    # Initialize Web3 client
    web3_client = Web3ClientImpl()
    network = NetworkType(settings.BLOCKCHAIN_NETWORK.value)
    
    try:
        connected = await web3_client.connect(network)
        if connected:
            logger.info("✅ Blockchain connection established", network=network.value)
            app.state.web3_client = web3_client
        else:
            logger.error("❌ Failed to connect to blockchain", network=network.value)
            app.state.web3_client = None
    except Exception as e:
        logger.error("❌ Blockchain connection error", error=str(e))
        app.state.web3_client = None
    
    # Add any other startup tasks here
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Art Platform API")
    
    # Cleanup resources
    if hasattr(app.state, 'web3_client') and app.state.web3_client:
        # Cleanup Web3 client if needed
        pass
    
    logger.info("✅ Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise-grade blockchain art platform with NFT minting and marketplace",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Setup application middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware (for production)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    # Request logging and metrics middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "📥 Request received",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            REQUEST_DURATION.observe(duration)
            
            # Log response
            logger.info(
                "📤 Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=f"{duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Update error metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            
            logger.error(
                "❌ Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration=f"{duration:.3f}s"
            )
            
            raise


def setup_routes(app: FastAPI) -> None:
    """Setup application routes"""
    
    @app.get("/", tags=["Health"])
    async def root():
        """Root endpoint with basic API information"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs_url": "/docs" if settings.DEBUG else None,
            "status": "healthy"
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check(settings: Any = Depends(get_settings)):
        """Comprehensive health check endpoint"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {}
        }
        
        # Check Web3 connection
        if hasattr(app.state, 'web3_client') and app.state.web3_client:
            try:
                is_connected = await app.state.web3_client.is_connected()
                health_status["services"]["blockchain"] = {
                    "status": "healthy" if is_connected else "unhealthy",
                    "network": settings.BLOCKCHAIN_NETWORK
                }
            except Exception as e:
                health_status["services"]["blockchain"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health_status["services"]["blockchain"] = {
                "status": "not_configured"
            }
        
        # Check if any service is unhealthy
        if any(service.get("status") == "unhealthy" for service in health_status["services"].values()):
            health_status["status"] = "unhealthy"
            return JSONResponse(status_code=503, content=health_status)
        
        return health_status
    
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        if not settings.PROMETHEUS_METRICS:
            raise HTTPException(status_code=404, detail="Metrics disabled")
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/blockchain/info", tags=["Blockchain"])
    async def blockchain_info():
        """Get blockchain network information"""
        if not hasattr(app.state, 'web3_client') or not app.state.web3_client:
            raise HTTPException(status_code=503, detail="Blockchain not available")
        
        try:
            network_info = await app.state.web3_client.get_network_info()
            return {
                "connected": True,
                "network_info": network_info,
                "contracts": {
                    "nft": settings.NFT_CONTRACT_ADDRESS,
                    "marketplace": settings.MARKETPLACE_CONTRACT_ADDRESS
                }
            }
        except Exception as e:
            logger.error("Failed to get blockchain info", error=str(e))
            raise HTTPException(status_code=503, detail="Failed to get blockchain info")
    
    @app.post("/wallet/create", tags=["Wallet"])
    async def create_wallet(password: str = "default"):
        """Create a new wallet"""
        if not hasattr(app.state, 'web3_client') or not app.state.web3_client:
            raise HTTPException(status_code=503, detail="Blockchain not available")
        
        try:
            BLOCKCHAIN_OPERATIONS.labels(operation="create_wallet", status="started").inc()
            
            address, private_key = await app.state.web3_client.create_wallet(password)
            
            BLOCKCHAIN_OPERATIONS.labels(operation="create_wallet", status="success").inc()
            
            return {
                "address": str(address),
                "private_key": private_key,  # In production, this should be encrypted/secured
                "warning": "Store your private key securely. It cannot be recovered if lost."
            }
        except Exception as e:
            BLOCKCHAIN_OPERATIONS.labels(operation="create_wallet", status="error").inc()
            logger.error("Failed to create wallet", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to create wallet")
    
    @app.get("/wallet/{address}/balance", tags=["Wallet"])
    async def get_wallet_balance(address: str):
        """Get wallet balance"""
        if not hasattr(app.state, 'web3_client') or not app.state.web3_client:
            raise HTTPException(status_code=503, detail="Blockchain not available")
        
        try:
            from app.core.ports.web3_client import WalletAddress
            wallet_address = WalletAddress(address)
            balance = await app.state.web3_client.get_balance(wallet_address)
            
            return {
                "address": address,
                "balance": str(balance),
                "unit": "ETH"
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error("Failed to get wallet balance", error=str(e), address=address)
            raise HTTPException(status_code=500, detail="Failed to get wallet balance")


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers"""
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("Validation error", error=str(exc), url=str(request.url))
        return JSONResponse(
            status_code=400,
            content={"error": "Validation Error", "detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            error=str(exc),
            url=str(request.url),
            method=request.method,
            exc_info=True
        )
        
        if settings.DEBUG:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "detail": str(exc)}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
            )


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly (for development)"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1 if settings.RELOAD else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    ) 