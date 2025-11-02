#!/bin/bash
# Test runner script with various options

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Slack RAG Assistant Test Runner ===${NC}\n"

# Function to print section headers
print_header() {
    echo -e "\n${YELLOW}>>> $1${NC}\n"
}

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    "all")
        print_header "Running all tests with coverage"
        pytest
        ;;

    "unit")
        print_header "Running unit tests only"
        pytest tests/unit/ -v
        ;;

    "integration")
        print_header "Running integration tests only"
        pytest tests/integration/ -v
        ;;

    "fast")
        print_header "Running fast tests (excluding slow tests)"
        pytest -m "not slow" -v
        ;;

    "smoke")
        print_header "Running smoke tests"
        pytest -m smoke -v
        ;;

    "coverage")
        print_header "Running tests with detailed coverage report"
        pytest --cov=src --cov-report=term-missing --cov-report=html
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    "quick")
        print_header "Running quick test (fail fast, no coverage)"
        pytest -x --no-cov -v
        ;;

    "parallel")
        print_header "Running tests in parallel"
        pytest -n auto
        ;;

    "watch")
        print_header "Running tests in watch mode"
        pytest-watch
        ;;

    "failed")
        print_header "Re-running failed tests only"
        pytest --lf -v
        ;;

    "verbose")
        print_header "Running tests with maximum verbosity"
        pytest -vv --tb=long
        ;;

    "clean")
        print_header "Cleaning test artifacts"
        rm -rf .pytest_cache htmlcov .coverage
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}Test artifacts cleaned${NC}"
        ;;

    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Available test types:"
        echo "  all         - Run all tests with coverage (default)"
        echo "  unit        - Run only unit tests"
        echo "  integration - Run only integration tests"
        echo "  fast        - Run fast tests (exclude slow)"
        echo "  smoke       - Run smoke tests"
        echo "  coverage    - Run with detailed coverage report"
        echo "  quick       - Fail fast, no coverage"
        echo "  parallel    - Run tests in parallel"
        echo "  watch       - Watch mode (requires pytest-watch)"
        echo "  failed      - Re-run failed tests only"
        echo "  verbose     - Maximum verbosity"
        echo "  clean       - Clean test artifacts"
        echo ""
        exit 1
        ;;
esac

# Check test result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests passed successfully!${NC}\n"
else
    echo -e "\n${RED}✗ Tests failed!${NC}\n"
    exit 1
fi
