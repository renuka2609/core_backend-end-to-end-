# Running Tenant Isolation Tests

## Quick Start

```bash
# Navigate to project root
cd d:\AIDS\internship\core_backend(end to end)

# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Run the comprehensive test suite
python test_cross_tenant_access_denial.py
```

Expected output:
```
================================================================================
CROSS-TENANT ACCESS DENIAL INTEGRATION TESTS
================================================================================

[test data setup messages...]

TEST: Assessment List Isolation
✅ PASS | Org1 user sees only Org1 assessments in list
   Status: 200 (expected 200)

[... more test results ...]

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 15
✅ Passed: 15
❌ Failed: 0
================================================================================
```

## Django Test Runner (Alternative)

```bash
# Run using Django's test framework
python manage.py test test_cross_tenant_access_denial

# Run with verbosity
python manage.py test test_cross_tenant_access_denial -v 2

# Run specific test class
python manage.py test test_cross_tenant_access_denial.TestCrossTenantAccessDenial
```

## Test Coverage

### Test Categories

#### List Isolation Tests (6 tests)
Verify that list endpoints only return user's org data:
- Assessment list
- Review list
- Template list
- Vendor list
- Evidence list
- Response list

#### Detail Access Denial Tests (6 tests)
Verify that accessing another org's resource returns 403 Forbidden:
- Assessment detail (403)
- Review detail (403)
- Template detail (403)
- Vendor detail (403)
- Evidence detail (403)
- Response detail (403)

#### Mutation Tests (2 tests)
Verify that modifications to other org's resources are denied:
- Update/PATCH operation (403)
- Delete operation (403)

#### Authentication Tests (1 test)
Verify that unauthenticated requests are denied:
- Unauthenticated list access (401)

## Test Data Flow

### Initial Setup
1. Create Organization 1 and Organization 2
2. Create users in each organization (admin/reviewer roles)
3. Create test resources (assessments, reviews, etc.) in each org

### Test Execution
1. Authenticate as Org1 user
2. Attempt various operations
3. Verify 200 OK for own org data
4. Verify 403 Forbidden for cross-org data
5. Verify 401 Unauthorized for unauthenticated

### Cleanup
- Test data automatically created fresh for each run
- Uses Django test database isolation
- Safe to run multiple times

## Customizing Tests

### Add New Test Case

```python
def test_new_feature_isolation(self):
    """Test: New feature endpoint respects tenant boundaries."""
    print("\n" + "-" * 80)
    print("TEST: New Feature Isolation")
    print("-" * 80)
    
    # User from org1 should only see org1 resources
    self.client.force_authenticate(user=self.user_org1_admin)
    resp = self.client.get('/api/new-feature/')
    
    passed = (resp.status_code == status.HTTP_200_OK and 
             len(resp.data) == 1)
    
    self.log_test(
        "Org1 user sees only Org1 new-feature resources",
        resp.status_code,
        status.HTTP_200_OK,
        passed
    )
```

Then call it from `run_all_tests()`:
```python
def run_all_tests(self):
    # ... existing tests ...
    self.test_new_feature_isolation()  # Add here
```

## Debugging Failed Tests

### Enable Verbose Output

Modify test file to add debugging:
```python
def test_assessment_detail_cross_tenant_deny(self):
    # ... setup ...
    
    resp = self.client.get(f'/api/assessments/{self.assessment_org2.id}/')
    
    print(f"\nDebug - Response status: {resp.status_code}")
    print(f"Debug - Response data: {resp.data}")
    print(f"Debug - Assessment ID: {self.assessment_org2.id}")
    print(f"Debug - Assessment org: {self.assessment_org2.org.id}")
    print(f"Debug - User org: {self.user_org1_admin.org.id}")
    
    passed = resp.status_code == status.HTTP_403_FORBIDDEN
```

### Common Issues

| Issue | Solution |
|-------|----------|
| 404 Not Found on endpoint | Verify API URL in test matches urls.py routing |
| 200 OK instead of 403 | Check mixin imported correctly in ViewSet |
| 500 Server Error | Check tenant_filter_field matches model field name |
| AttributeError: user.org | Verify test user has org attribute set |

## Continuous Integration

### GitHub Actions / CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tenant isolation tests
      run: |
        python manage.py migrate
        python test_cross_tenant_access_denial.py
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running tenant isolation tests..."
python test_cross_tenant_access_denial.py
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

## Performance Considerations

### Test Execution Time
- **Expected**: 5-30 seconds (varies by system)
- **Slow point**: Database setup with 2 orgs and multiple resources
- **Per-test time**: ~200-500ms

### Optimization
If running frequently:
```python
# Skip cleanup if not needed
# Comment out Organization cleanup in setup_test_data()
```

## Troubleshooting

### Test won't run
```bash
# Ensure Django is configured
python manage.py shell  # Should work

# Ensure test file is executable
chmod +x test_cross_tenant_access_denial.py
```

### Import errors
```bash
# Ensure you're in project root
cd d:\AIDS\internship\core_backend(end to end)

# Check Python path
python -c "import django; print(django.__file__)"

# Verify settings module
echo %DJANGO_SETTINGS_MODULE% (should be config.settings)
```

### Database errors
```bash
# Reset database
python manage.py migrate --run-syncdb

# Clear test database cache
rm -rf db.sqlite3

# Re-run tests
python test_cross_tenant_access_denial.py
```

## Integration with Existing Tests

Run alongside other tests:
```bash
# All tests in sequence
python manage.py test

# Just tenant isolation
python manage.py test test_cross_tenant_access_denial

# List all available tests
python manage.py test --list-labels
```

## Documentation

- Full implementation guide: `TENANT_ISOLATION_POLICY.md`
- Verification report: `TENANT_ISOLATION_VERIFICATION.md`
- Quick start guide: `IMPLEMENTATION_QUICK_START.md`

---

**Questions?** Check the TENANT_ISOLATION_POLICY.md for implementation details.
