#!/bin/bash

# Integration Test Script
# Tests the complete system end-to-end

echo "🧪 Running Integration Tests..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    test_name=$1
    command=$2
    
    echo "Testing: $test_name"
    if eval $command > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# 1. Check Python environment
echo "="*60
echo "1. Environment Checks"
echo "="*60
run_test "Python version >= 3.10" "python3 --version | grep -E '3\.(1[0-9]|[2-9][0-9])'"
run_test "Virtual environment exists" "test -d venv"
run_test "Requirements installed" "pip show fastapi transformers torch > /dev/null 2>&1"

# 2. Check project structure
echo "="*60
echo "2. Project Structure"
echo "="*60
run_test "Data directory exists" "test -d data/raw/images && test -d data/raw/annotations"
run_test "Backend directory exists" "test -d backend && test -f backend/main.py"
run_test "Frontend directory exists" "test -d frontend && test -f frontend/package.json"
run_test "Models directory exists" "test -d models && test -f models/train_codet5.py"
run_test "Preprocessing directory exists" "test -d preprocessing"

# 3. Test Python modules
echo "="*60
echo "3. Python Module Tests"
echo "="*60

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

run_test "Text parser test" "python tests/test_parser.py"

# 4. Check data
echo "="*60
echo "4. Data Checks"
echo "="*60
IMAGE_COUNT=$(ls data/raw/images/*.png 2>/dev/null | wc -l)
ANNOTATION_COUNT=$(ls data/raw/annotations/*.txt 2>/dev/null | wc -l)

echo "Images found: $IMAGE_COUNT"
echo "Annotations found: $ANNOTATION_COUNT"

if [ $ANNOTATION_COUNT -gt 4000 ]; then
    echo -e "${GREEN}✅ PASSED${NC}: Annotations exist (~4k)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Expected ~4000 annotations, found $ANNOTATION_COUNT"
fi
echo ""

# 5. Test backend API (if running)
echo "="*60
echo "5. Backend API Tests"
echo "="*60

# Check if backend is running
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "Backend is running on port 8000"
    run_test "Health endpoint" "curl -s http://localhost:8000/api/v1/health | grep -q 'ok'"
    run_test "Parse endpoint" "curl -s -X POST http://localhost:8000/api/v1/parse -H 'Content-Type: application/json' -d '{\"text\":\"The living room is large.\"}' | grep -q 'json'"
    
    echo "Running full API tests..."
    python tests/test_api.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: API tests"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}: API tests"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: Backend not running (start with: cd backend && uvicorn main:app)"
fi
echo ""

# 6. Test frontend (if running)
echo "="*60
echo "6. Frontend Tests"
echo "="*60

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}: Frontend is accessible"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: Frontend not running (start with: cd frontend && npm run dev)"
fi
echo ""

# 7. Documentation checks
echo "="*60
echo "7. Documentation Checks"
echo "="*60
run_test "README exists" "test -f README.md"
run_test "QUICKSTART exists" "test -f QUICKSTART.md"
run_test "API docs exist" "test -f docs/api_reference.md"
run_test "Training guide exists" "test -f docs/training_guide.md"

# Summary
echo ""
echo "="*60
echo "📊 TEST SUMMARY"
echo "="*60
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "System is ready to use:"
    echo "1. Process data: ./scripts/run_preprocessing.sh"
    echo "2. Start backend: cd backend && python -m uvicorn main:app --reload"
    echo "3. Start frontend: cd frontend && npm run dev"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the output above.${NC}"
    exit 1
fi

