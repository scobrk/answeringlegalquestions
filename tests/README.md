# NSW Revenue AI Testing Framework

A comprehensive testing and validation framework for the expanded NSW Revenue system, designed to validate 67+ revenue types with production-ready accuracy and performance.

## Overview

This testing framework provides complete validation coverage for the NSW Revenue AI system, ensuring it can handle all NSW revenue types with the required accuracy, performance, and reliability for production deployment.

## Testing Scope

### 🎯 Test Categories

1. **Functional Testing** - All 67 revenue types respond accurately
2. **Performance Testing** - System handles 50,000+ chunks with <2s response time
3. **Integration Testing** - FastAPI, agents, and vector store work together
4. **Accuracy Testing** - Responses are legally accurate and complete
5. **Edge Case Testing** - Complex multi-tax scenarios and cross-references

### 📊 Coverage

- **67 Revenue Types**: Complete coverage across all NSW revenue categories
- **5 Test Suites**: Functional, Performance, Accuracy, Integration, Edge Cases
- **Production Criteria**: >95% accuracy, <2s response time, 100% revenue coverage

## Quick Start

### Prerequisites

```bash
# Ensure the NSW Revenue AI system is running
python fastapi_app.py

# Install additional testing dependencies if needed
pip install pytest aiohttp matplotlib seaborn numpy pandas
```

### Run All Tests

```bash
# Run comprehensive test suite (all tests)
python tests/run_comprehensive_tests.py

# Run with specific API URL
python tests/run_comprehensive_tests.py --api-url http://localhost:8080
```

### Run Specific Test Suites

```bash
# Run only functional tests
python tests/run_comprehensive_tests.py --suites functional

# Run performance and accuracy tests
python tests/run_comprehensive_tests.py --suites performance accuracy

# Run with verbose logging
python tests/run_comprehensive_tests.py --verbose
```

### Run Individual Test Suites

```bash
# Functional tests only
python tests/functional_test_suite.py

# Performance tests only
python tests/performance_test_suite.py

# Accuracy validation only
python tests/accuracy_validation_suite.py

# Integration tests only
python tests/integration_test_suite.py

# Edge case tests only
python tests/edge_case_test_suite.py
```

## Test Suite Details

### 1. Functional Test Suite

**Purpose**: Validate that all 67 revenue types respond correctly with appropriate accuracy and completeness.

**Key Features**:
- Revenue type coverage testing for all NSW taxes
- Response quality validation
- Confidence scoring validation
- Citation accuracy checking
- Multi-tax scenario handling

**Pass Criteria**:
- 95% of tests pass
- All revenue types covered
- Average confidence >70%
- Response time <2s per query

```bash
python tests/functional_test_suite.py
```

### 2. Performance Test Suite

**Purpose**: Validate system performance under various load conditions and ensure <2s response times.

**Key Features**:
- Baseline response time testing
- Concurrent load testing (5-50 users)
- Stress testing to find breaking points
- Memory usage monitoring
- Sustained load testing (15+ minutes)
- Query complexity performance analysis

**Pass Criteria**:
- Average response time <2s
- P95 response time <1.5s
- Memory usage <500MB
- Handle 10+ concurrent users
- System remains stable under load

```bash
python tests/performance_test_suite.py
```

### 3. Accuracy Validation Suite

**Purpose**: Validate legal accuracy, calculation precision, and citation correctness with >95% accuracy.

**Key Features**:
- Legal fact validation against known NSW legislation
- Tax calculation precision testing
- Citation accuracy verification
- Rate and threshold validation
- Multi-dimensional accuracy scoring

**Pass Criteria**:
- Overall accuracy >95%
- Legal accuracy >90%
- Calculation accuracy >95%
- Citation accuracy >80%
- No hallucinated legal references

```bash
python tests/accuracy_validation_suite.py
```

### 4. Integration Test Suite

**Purpose**: Validate integration between FastAPI, agents, vector store, and all system components.

**Key Features**:
- Component health testing
- API endpoint integration
- Agent-to-agent communication
- Vector store integration
- Database connectivity
- Error handling validation
- End-to-end flow testing

**Pass Criteria**:
- 90% of integration tests pass
- All components healthy
- API endpoints respond correctly
- Agent chain works properly
- Error handling graceful

```bash
python tests/integration_test_suite.py
```

### 5. Edge Case Test Suite

**Purpose**: Test complex multi-tax scenarios, boundary conditions, and edge cases.

**Key Features**:
- Boundary value testing (thresholds, limits)
- Complex multi-tax calculations
- Invalid input handling
- Extreme value processing
- Temporal queries (historical/future)
- Ambiguous query handling
- Error recovery testing

**Pass Criteria**:
- 80% edge case robustness
- Graceful error handling
- No system crashes
- Appropriate responses to invalid input
- Complex scenarios handled correctly

```bash
python tests/edge_case_test_suite.py
```

## Test Data

### Revenue Types Covered (67 total)

**Property Taxes (12 types)**:
- Land Tax, Conveyance Duty, Mortgage Duty, Lease Duty
- Business Sale Duty, First Home Buyer Schemes
- Foreign Purchaser Duty, Property Tax Exemptions
- Strata Levies, Vacant Land Tax, Premium Property Tax
- Developer Contributions

**Business Taxes (15 types)**:
- Payroll Tax, Casino Tax, Racing Tax, Club Gaming Tax
- Online Gambling Tax, Lotteries Tax, Keno Tax
- Insurance Tax, Petroleum Products Tax, Tobacco Tax
- Liquor Tax, Business Registration, Corporate Compliance
- Professional Licensing, Trade Licensing

**Vehicle Taxes (8 types)**:
- Motor Vehicle Tax, Registration Fees, CTP Insurance Levy
- Vehicle Inspection Fees, Electric Vehicle Concessions
- Heavy Vehicle Taxes, Trailer Registration, Personalized Plates

**Mining & Resources (6 types)**:
- Coal Royalties, Petroleum Royalties, Mineral Royalties
- Offshore Petroleum Royalties, Sand/Gravel Royalties
- Quarry Products Royalties

**Environmental Taxes (7 types)**:
- Waste Levy, Container Deposit Levy, Plastic Bag Levy
- Carbon Pricing, Environment Protection Levy
- Biodiversity Offset Levy, Native Vegetation Levy

**Health & Safety Levies (5 types)**:
- Ambulance Levy, Emergency Services Levy
- Health Insurance Levy, Workers Compensation Levy
- Fire Brigade Levy

**Urban Services (4 types)**:
- Parking Space Levy, Congestion Levy
- Infrastructure Levy, Transport Levy

**Miscellaneous Revenues (10+ types)**:
- Fines & Penalties, Court Fees, Statutory Fees
- Licensing Fees, Planning Fees, Building Approval Fees
- Water Usage Fees, Fisheries Licenses, Hunting Licenses
- National Parks Fees

## Production Readiness Criteria

The testing framework evaluates production readiness against these criteria:

| Criterion | Target | Weight |
|-----------|--------|---------|
| Functional Pass Rate | ≥95% | Critical |
| Average Response Time | <2.0s | Critical |
| Accuracy Score | ≥95% | Critical |
| Integration Pass Rate | ≥90% | High |
| Edge Case Robustness | ≥80% | Medium |
| Revenue Type Coverage | 100% | Critical |

### Production Ready Status

✅ **PRODUCTION READY** if:
- All critical criteria met
- No critical issues identified
- System stable under load
- Comprehensive test coverage

❌ **NOT PRODUCTION READY** if:
- Any critical criterion failed
- Critical issues identified
- System unstable or crashes
- Incomplete coverage

## Test Reports

### Generated Reports

All test runs generate comprehensive reports in `tests/reports/`:

1. **JSON Reports**: Machine-readable detailed results
   - `comprehensive_test_report_YYYYMMDD_HHMMSS.json`
   - `functional_test_report_YYYYMMDD_HHMMSS.json`
   - `performance_report_YYYYMMDD_HHMMSS.json`
   - `accuracy_validation_report_YYYYMMDD_HHMMSS.json`
   - `integration_test_report_YYYYMMDD_HHMMSS.json`
   - `edge_case_test_report_YYYYMMDD_HHMMSS.json`

2. **HTML Summary**: Human-readable dashboard
   - `test_summary_YYYYMMDD_HHMMSS.html`

3. **Database Storage**: SQLite database for historical tracking
   - `test_results.db`

### Report Contents

Each report includes:
- **Executive Summary**: Pass/fail status, key metrics
- **Detailed Results**: Individual test results and analysis
- **Performance Metrics**: Response times, throughput, resource usage
- **Accuracy Scores**: Legal, calculation, and citation accuracy
- **Issues & Recommendations**: Specific improvement suggestions
- **Trend Analysis**: Performance over time (if historical data available)

## Configuration

### Test Configuration

Default test configuration in `tests/test_framework_architecture.py`:

```python
default_config = {
    'api_base_url': 'http://localhost:8080',
    'max_concurrent_tests': 10,
    'timeout_seconds': 30,
    'retry_attempts': 3,
    'accuracy_threshold': 0.95,
    'performance_threshold_ms': 2000,
    'enable_stress_testing': False,
    'results_db_path': 'test_results.db',
    'test_data_path': 'tests/test_data/',
    'reports_output_path': 'tests/reports/'
}
```

### Customization

Override configuration by creating `tests/config.json`:

```json
{
    "api_base_url": "http://your-api-url:8080",
    "accuracy_threshold": 0.98,
    "performance_threshold_ms": 1500,
    "enable_stress_testing": true,
    "max_concurrent_tests": 20
}
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: NSW Revenue AI Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Start NSW Revenue AI
      run: python fastapi_app.py &

    - name: Wait for service
      run: sleep 30

    - name: Run comprehensive tests
      run: python tests/run_comprehensive_tests.py

    - name: Upload test reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: tests/reports/
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   ```bash
   # Ensure NSW Revenue AI is running
   curl http://localhost:8080/api/health

   # Check if port is correct
   python tests/run_comprehensive_tests.py --api-url http://localhost:8000
   ```

2. **Test Timeouts**
   ```bash
   # Increase timeout in config
   # Or run with fewer concurrent tests
   python tests/run_comprehensive_tests.py --verbose
   ```

3. **Missing Dependencies**
   ```bash
   pip install pytest aiohttp numpy pandas matplotlib seaborn
   ```

4. **Permission Errors**
   ```bash
   # Ensure write permissions for reports directory
   chmod 755 tests/reports/
   ```

### Debug Mode

```bash
# Run with maximum verbosity
python tests/run_comprehensive_tests.py --verbose

# Run single test suite for debugging
python tests/functional_test_suite.py

# Check individual component health
python -c "
from tests.integration_test_suite import IntegrationTestSuite
import asyncio
suite = IntegrationTestSuite()
print(asyncio.run(suite._test_api_health()))
"
```

## Contributing

### Adding New Tests

1. **Revenue Type Tests**: Add to `tests/test_data/comprehensive_revenue_test_cases.json`
2. **Performance Tests**: Extend `tests/performance_test_suite.py`
3. **Accuracy Tests**: Add to `tests/accuracy_validation_suite.py`
4. **Edge Cases**: Extend `tests/edge_case_test_suite.py`

### Test Case Format

```json
{
  "id": "REV001",
  "name": "New Revenue Type Test",
  "revenue_type": "new_revenue_type",
  "test_type": "functional",
  "question": "Test question about new revenue type?",
  "expected_revenue_types": ["new_revenue_type"],
  "expected_confidence_min": 0.8,
  "expected_response_time_max": 2.0,
  "validation_criteria": {
    "must_calculate_correctly": true,
    "must_cite_legislation": true
  },
  "complexity_level": "moderate",
  "priority": "high"
}
```

## Support

For issues, questions, or contributions:

1. **Check Reports**: Review generated test reports for detailed analysis
2. **Debug Logs**: Run with `--verbose` for detailed logging
3. **Component Health**: Use integration tests to check individual components
4. **Performance**: Monitor system resources during testing

---

**Framework Version**: 1.0
**Compatible with**: NSW Revenue AI v1.0+
**Last Updated**: 2024
**Test Coverage**: 67 Revenue Types
**Production Ready**: Yes (when all criteria met)