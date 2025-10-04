"""
Quick test script to verify the setup
Tests imports and basic functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from src import config
        print("✅ config imported successfully")
    except Exception as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    try:
        from src import models
        print("✅ models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    try:
        from src import calculator
        print("✅ calculator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import calculator: {e}")
        return False
    
    try:
        from src import api
        print("✅ api imported successfully")
    except Exception as e:
        print(f"❌ Failed to import api: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values"""
    print("\nTesting configuration...")
    
    from src import config
    
    print(f"  Flask Host: {config.FLASK_HOST}")
    print(f"  Flask Port: {config.FLASK_PORT}")
    print(f"  Log Level: {config.LOG_LEVEL}")
    print(f"  Pension Contribution Rate: {config.PENSION_CONTRIBUTION_RATE}")
    print(f"  Minimum Pension 2025: {config.MINIMUM_PENSION_2025}")
    print("✅ Configuration loaded successfully")
    
    return True

def test_models():
    """Test model creation"""
    print("\nTesting models...")
    
    from src.models import UserData, PensionCalculationRequest
    
    # Test UserData
    try:
        user_data = UserData(
            age=30,
            gender="male",
            gross_salary=8000.0,
            work_start_year=2015
        )
        print(f"✅ UserData created: age={user_data.age}, salary={user_data.gross_salary}")
    except Exception as e:
        print(f"❌ Failed to create UserData: {e}")
        return False
    
    # Test PensionCalculationRequest
    try:
        request = PensionCalculationRequest(
            user_data={
                "age": 30,
                "gender": "male",
                "gross_salary": 8000.0,
                "work_start_year": 2015
            }
        )
        print(f"✅ PensionCalculationRequest created")
    except Exception as e:
        print(f"❌ Failed to create PensionCalculationRequest: {e}")
        return False
    
    return True

def test_api_app():
    """Test Flask app creation"""
    print("\nTesting Flask app...")
    
    from src.api import app
    
    print(f"✅ Flask app created: {app.name}")
    print(f"  Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"    - {rule.endpoint}: {rule.rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("PENSION CALCULATOR - SETUP TEST")
    print("="*60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Models", test_models),
        ("Flask App", test_api_app),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nYour setup is ready. Next steps:")
        print("1. Add PPLX_API_KEY to .env file")
        print("2. Run: python run.py")
        print("3. Test: curl http://localhost:5000/health")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease check:")
        print("1. Have you run: pip install -r requirements.txt ?")
        print("2. Are all dependencies installed?")
    print("="*60)

if __name__ == "__main__":
    main()
