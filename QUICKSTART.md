# 🚀 Quick Start - Testing Guide

Get your blockchain wallet and smart contract platform running for testing in under 5 minutes.

## ⚡ Prerequisites Check

```bash
# Check if you have the required tools
python --version   # Should be 3.9+
node --version     # Should be 18+
uv --version       # If not installed: curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 🏗️ Quick Setup

### 1. Clone & Environment Setup
```bash
git clone <repository-url>
cd smart-contract-platform

# Copy environment files
cp .env.example .env
cp blockchain/.env.example blockchain/.env
```

### 2. Backend Setup (Python)
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (fast with uv)
uv pip install -r requirements.txt

# Verify installation
python -c "import fastapi, web3; print('✅ Backend dependencies installed')"
```

### 3. Blockchain Setup (Node.js)
```bash
cd ../blockchain  # Go to blockchain directory

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Verify installation
npx hardhat --version
echo "✅ Blockchain setup complete"
```

## 🧪 Run Tests

### Smart Contract Tests
```bash
cd blockchain

# Run all contract tests
npm test

# Run specific test
npm test test/TokenContract.test.js

# Run with gas reporting
npm run test:gas
```

### Backend Tests
```bash
cd backend
source venv/bin/activate  # Activate venv

# Run all backend tests
pytest

# Run only unit tests (fast)
pytest -m unit

# Run with coverage
pytest --cov=app
```

### Quick Test Verification
```bash
# Test smart contracts (from blockchain/)
npm test

# Test backend (from backend/ with venv activated)
pytest tests/unit/ -v

# If both pass, you're ready! ✅
```

## 🔍 Quick Verification

### Check Smart Contract Compilation
```bash
cd blockchain
npx hardhat compile
# Should see: "Compiled X Solidity files successfully"
```

### Check Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/docs
```

### Test Blockchain Connection
```bash
cd blockchain
npx hardhat node
# Should start local blockchain at http://localhost:8545
```

## 🚨 Troubleshooting

### Common Issues

**❌ "uv not found"**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**❌ "Module not found" (Python)**
```bash
cd backend
source venv/bin/activate  # Make sure venv is activated
uv pip install -r requirements.txt
```

**❌ "npm install fails"**
```bash
cd blockchain
rm -rf node_modules package-lock.json
npm install
```

**❌ "hardhat not found"**
```bash
cd blockchain
npm install -g hardhat  # or use npx hardhat
```

## 🎯 Test Categories

### Quick Tests (< 30 seconds)
```bash
# Smart contracts - basic functionality
cd blockchain && npm test

# Backend - unit tests only
cd backend && source venv/bin/activate && pytest -m unit
```

### Security Tests
```bash
# Backend security tests
cd backend && source venv/bin/activate && pytest -m security

# Contract security tests
cd blockchain && npm run test:security
```

### Full Test Suite
```bash
# Everything (takes 2-5 minutes)
cd blockchain && npm test && cd ../backend && source venv/bin/activate && pytest
```

## 📊 Success Indicators

✅ **Smart Contracts Ready:**
- `npm test` passes all tests
- Contracts compile without errors
- Gas reports show reasonable usage

✅ **Backend Ready:**
- `pytest` passes all tests
- No private key exposure in logs
- All wallet operations work

✅ **Integration Ready:**
- Local blockchain node runs
- Backend connects to blockchain
- End-to-end tests pass

## 🔥 Pro Tips

### Speed Up Development
```bash
# Use test watchers
cd blockchain && npm run test:watch  # Re-run tests on file changes

# Run only failed tests
cd backend && pytest --lf  # Last failed
```

### Debug Mode
```bash
# Verbose output
cd blockchain && npm test -- --verbose
cd backend && pytest -v -s

# Debug specific test
pytest tests/unit/test_wallet.py::test_create_wallet -v -s
```

### Quick Environment Reset
```bash
# Reset blockchain state
cd blockchain && npx hardhat clean && npx hardhat compile

# Reset Python environment
cd backend && rm -rf venv && python -m venv venv && source venv/bin/activate && uv pip install -r requirements.txt
```

## 🎮 Ready to Code!

Once all tests pass, you're ready for development:

1. **Smart Contracts**: Edit in `blockchain/contracts/`
2. **Backend**: Edit in `backend/app/`
3. **Tests**: Add tests as you develop

**Happy testing!** 🚀

---

Need more details? Check the full [README.md](./README.md) for comprehensive documentation. 