import pytest
import sys
from pathlib import Path
import shutil

def setup_test_environment():
    """Setup test environment and directories"""
    test_dirs = ['test_output', 'test_assets', 'test_logs']
    test_root = Path(__file__).parent / 'tests'

    for dir_name in test_dirs:
        dir_path = test_root / dir_name
        dir_path.mkdir(exist_ok=True)

def cleanup_test_environment():
    """Clean up test directories after testing"""
    test_root = Path(__file__).parent / 'tests'
    test_dirs = ['test_output', 'test_assets', 'test_logs']

    for dir_name in test_dirs:
        dir_path = test_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)

if __name__ == '__main__':
    try:
        setup_test_environment()

        # Run pytest with coverage
        exit_code = pytest.main()

        # Clean up test environment
        cleanup_test_environment()

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        cleanup_test_environment()
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        cleanup_test_environment()
        sys.exit(1)