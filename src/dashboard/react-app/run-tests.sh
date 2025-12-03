#!/bin/bash

# Run regression tests for React Dashboard

echo "Running React Dashboard Regression Tests..."
echo "=========================================="

# Add test script to package.json temporarily
npx json -I -f package.json -e 'this.scripts.test="jest"'
npx json -I -f package.json -e 'this.scripts["test:coverage"]="jest --coverage"'

# Run the tests
npm test -- --passWithNoTests

echo ""
echo "Test execution complete!"