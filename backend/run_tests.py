#!/usr/bin/env python3
"""
Test Runner for Iteration 1
Run comprehensive tests for all Iteration 1 functionality
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Main test runner"""
    print("CashFlow AI - Iteration 1 Test Suite")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if MongoDB is running
    print("Checking MongoDB connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017/cashflow?authSource=admin")
        client.admin.command('ping')
        print("MongoDB is running")
        client.close()
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Please start MongoDB with: docker-compose up -d mongo")
        sys.exit(1)
    
    # Test suites to run
    test_suites = [
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1Authentication -v",
            "description": "Authentication Tests"
        },
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1CSVIngestion -v",
            "description": "CSV Ingestion Tests"
        },
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1Transactions -v",
            "description": "Transaction Management Tests"
        },
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1Dashboard -v",
            "description": "Dashboard Analytics Tests"
        },
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1Integration -v",
            "description": "Integration Tests"
        },
        {
            "command": "python -m pytest test_iteration_1.py::TestIteration1Performance -v",
            "description": "Performance Tests"
        }
    ]
    
    # Run all test suites
    results = []
    total_tests = 0
    passed_tests = 0
    
    for suite in test_suites:
        success = run_command(suite["command"], suite["description"])
        results.append((suite["description"], success))
        
        if success:
            passed_tests += 1
            print(f"PASSED {suite['description']}")
        else:
            print(f"FAILED {suite['description']}")
        
        total_tests += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{status:<12} {description}")
    
    print(f"\nTotal Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\nAll tests passed! Iteration 1 is ready for production.")
        return 0
    else:
        print(f"\n{total_tests - passed_tests} test suite(s) failed.")
        print("Please review the failures and fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
