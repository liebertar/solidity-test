#!/bin/bash

# Enterprise Blockchain Platform - Docker Quick Start
# One command to rule them all! 🚀

set -e

echo "🚀 Enterprise Blockchain Platform - Docker Setup"
echo "==============================================="
echo ""

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running! Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed! Please install it and try again."
    exit 1
fi

print_success "Docker and Docker Compose are ready!"

# Parse command line arguments
ACTION=${1:-"up"}

case $ACTION in
    "up"|"start")
        print_status "Starting Enterprise Blockchain Platform..."
        
        # Create shared directory if it doesn't exist
        mkdir -p shared
        
        # Start services
        print_status "Building and starting all services..."
        docker-compose up --build -d
        
        print_status "Waiting for services to be healthy..."
        sleep 30
        
        # Check service health
        print_status "Checking service health..."
        
        # Wait for backend to be ready
        for i in {1..30}; do
            if curl -s http://localhost:8001/health > /dev/null; then
                print_success "Backend API is healthy!"
                break
            fi
            print_status "Waiting for backend... ($i/30)"
            sleep 5
        done
        
        # Display service URLs
        echo ""
        echo "🎉 Enterprise Blockchain Platform is running!"
        echo "============================================="
        echo ""
        echo "🔗 Service URLs:"
        echo "  📡 API Documentation:    http://localhost:8001/docs"
        echo "  🏥 Health Check:         http://localhost:8001/health"
        echo "  📊 Metrics:             http://localhost:8001/metrics"
        echo "  ⛓️  Blockchain RPC:      http://localhost:8547"
        echo "  📊 Prometheus:          http://localhost:9091"
        echo "  📈 Grafana:             http://localhost:3002 (admin/admin123)"
        echo "  🗄️  Database:            localhost:5433 (blockchain_user/blockchain_password)"
        echo "  🔄 Redis:               localhost:6380"
        echo "  📁 IPFS:                http://localhost:8081"
        echo ""
        echo "🧪 Quick Test Commands:"
        echo "  curl http://localhost:8001/health"
        echo "  curl http://localhost:8001/blockchain/info"
        echo "  curl -X POST http://localhost:8001/wallet/create"
        echo ""
        echo "📖 View logs: docker-compose logs -f [service_name]"
        echo "🛑 Stop all:  ./start.sh stop"
        echo ""
        ;;
        
    "stop"|"down")
        print_status "Stopping Enterprise Blockchain Platform..."
        docker-compose down
        print_success "All services stopped!"
        ;;
        
    "restart")
        print_status "Restarting Enterprise Blockchain Platform..."
        docker-compose down
        docker-compose up --build -d
        print_success "Platform restarted!"
        ;;
        
    "logs")
        SERVICE=${2:-""}
        if [ -z "$SERVICE" ]; then
            print_status "Showing logs for all services..."
            docker-compose logs -f
        else
            print_status "Showing logs for service: $SERVICE"
            docker-compose logs -f $SERVICE
        fi
        ;;
        
    "clean")
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Cleaning up everything..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup complete!"
        else
            print_status "Cleanup cancelled."
        fi
        ;;
        
    "test")
        print_status "Running integration tests..."
        
        # Wait for services
        sleep 10
        
        echo "🧪 Testing API endpoints..."
        
        # Test health
        if curl -s http://localhost:8001/health | grep -q "healthy"; then
            print_success "✅ Health check passed"
        else
            print_error "❌ Health check failed"
        fi
        
        # Test blockchain info
        if curl -s http://localhost:8001/blockchain/info | grep -q "connected"; then
            print_success "✅ Blockchain connection test passed"
        else
            print_error "❌ Blockchain connection test failed"
        fi
        
        # Test wallet creation
        WALLET_RESPONSE=$(curl -s -X POST "http://localhost:8001/wallet/create" -H "Content-Type: application/json" -d '{"password": "test123"}')
        if echo "$WALLET_RESPONSE" | grep -q "address"; then
            print_success "✅ Wallet creation test passed"
            echo "   Created wallet: $(echo $WALLET_RESPONSE | grep -o '"address":"[^"]*"' | cut -d'"' -f4)"
        else
            print_error "❌ Wallet creation test failed"
        fi
        
        print_success "Integration tests completed!"
        ;;
        
    "status")
        print_status "Service Status:"
        docker-compose ps
        ;;
        
    "help"|*)
        echo "Enterprise Blockchain Platform - Docker Commands"
        echo "=============================================="
        echo ""
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up, start       Start all services (default)"
        echo "  stop, down      Stop all services"
        echo "  restart         Restart all services"
        echo "  logs [service]  Show logs (optionally for specific service)"
        echo "  test            Run integration tests"
        echo "  status          Show service status"
        echo "  clean           Remove all containers and volumes"
        echo "  help            Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./start.sh                    # Start platform"
        echo "  ./start.sh logs backend       # Show backend logs"
        echo "  ./start.sh test               # Run tests"
        echo "  ./start.sh clean              # Clean everything"
        echo ""
        ;;
esac 