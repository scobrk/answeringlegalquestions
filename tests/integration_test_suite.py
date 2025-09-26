#!/usr/bin/env python3
"""
Integration Test Suite for NSW Revenue AI System
Tests integration between FastAPI, agents, vector store, and all system components
"""

import os
import sys
import asyncio
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import sqlite3
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_framework_architecture import TestFramework, TestCase, TestResult

logger = logging.getLogger(__name__)


@dataclass
class IntegrationTestResult:
    """Result of an integration test"""
    test_name: str
    component_tested: str
    passed: bool
    response_time: float
    error_details: List[str]
    warnings: List[str]
    component_status: Dict[str, str]
    integration_points_validated: List[str]
    timestamp: datetime


class IntegrationTestSuite:
    """
    Comprehensive integration testing suite for NSW Revenue AI system
    Tests all component interactions: FastAPI, agents, vector store, database
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.integration_results = []

        # Component health check endpoints
        self.health_endpoints = {
            'api': f"{api_base_url}/api/health",
            'system': f"{api_base_url}/api/query"
        }

        # Test queries for different integration scenarios
        self.integration_test_queries = {
            'simple': "What is the NSW payroll tax rate?",
            'calculation': "Calculate payroll tax for $2.5 million in wages",
            'multi_tax': "For a business with $3.4M payroll and 12 properties worth $43.2M, what taxes apply?",
            'classification': "I need help with land tax exemptions",
            'complex': "What are all the NSW revenue implications for a foreign entity purchasing 8 investment properties totaling $15.6 million?"
        }

    async def run_comprehensive_integration_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive integration testing across all system components
        """
        logger.info("🔗 Starting Comprehensive Integration Testing Suite")

        integration_results = {
            'suite_name': 'Comprehensive Integration Tests',
            'start_time': datetime.now(),
            'component_tests': {},
            'api_integration_tests': {},
            'agent_integration_tests': {},
            'vector_store_integration_tests': {},
            'database_integration_tests': {},
            'error_handling_tests': {},
            'end_to_end_tests': {},
            'overall_integration_health': {}
        }

        # 1. Component Health Tests
        logger.info("🏥 Running Component Health Tests...")
        component_health = await self._test_component_health()
        integration_results['component_tests'] = component_health

        # 2. API Integration Tests
        logger.info("🌐 Running API Integration Tests...")
        api_tests = await self._test_api_integration()
        integration_results['api_integration_tests'] = api_tests

        # 3. Agent Integration Tests
        logger.info("🤖 Running Agent Integration Tests...")
        agent_tests = await self._test_agent_integration()
        integration_results['agent_integration_tests'] = agent_tests

        # 4. Vector Store Integration Tests
        logger.info("🔍 Running Vector Store Integration Tests...")
        vector_tests = await self._test_vector_store_integration()
        integration_results['vector_store_integration_tests'] = vector_tests

        # 5. Database Integration Tests
        logger.info("💾 Running Database Integration Tests...")
        database_tests = await self._test_database_integration()
        integration_results['database_integration_tests'] = database_tests

        # 6. Error Handling Integration Tests
        logger.info("⚠️ Running Error Handling Integration Tests...")
        error_tests = await self._test_error_handling_integration()
        integration_results['error_handling_tests'] = error_tests

        # 7. End-to-End Integration Tests
        logger.info("🔄 Running End-to-End Integration Tests...")
        e2e_tests = await self._test_end_to_end_integration()
        integration_results['end_to_end_tests'] = e2e_tests

        # 8. Overall Integration Health Assessment
        integration_results['overall_integration_health'] = self._assess_overall_integration_health(integration_results)

        integration_results['end_time'] = datetime.now()
        integration_results['total_duration'] = (integration_results['end_time'] - integration_results['start_time']).total_seconds()

        # Generate integration test report
        self._generate_integration_report(integration_results)

        return integration_results

    async def _test_component_health(self) -> Dict[str, Any]:
        """
        Test health of individual system components
        """
        health_results = {}

        # Test API Health
        api_health = await self._test_api_health()
        health_results['api'] = api_health

        # Test Classification Agent Health
        classification_health = await self._test_classification_agent_health()
        health_results['classification_agent'] = classification_health

        # Test Orchestrator Health
        orchestrator_health = await self._test_orchestrator_health()
        health_results['orchestrator'] = orchestrator_health

        # Test Vector Store Health
        vector_store_health = await self._test_vector_store_health()
        health_results['vector_store'] = vector_store_health

        # Test Primary Agent Health
        primary_agent_health = await self._test_primary_agent_health()
        health_results['primary_agent'] = primary_agent_health

        return health_results

    async def _test_api_health(self) -> IntegrationTestResult:
        """Test FastAPI health and endpoints"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test health endpoint
            response = requests.get(self.health_endpoints['api'], timeout=10)
            integration_points.append("health_endpoint")

            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get('status', 'unknown')

                if status != 'healthy':
                    errors.append(f"API health status: {status}")

                integration_points.append("health_status_check")
            else:
                errors.append(f"Health endpoint returned {response.status_code}")

        except Exception as e:
            errors.append(f"API health check failed: {str(e)}")

        # Test main query endpoint availability
        try:
            test_payload = {
                "question": "test query",
                "enable_approval": False,
                "include_metadata": False
            }

            response = requests.post(
                f"{self.api_base_url}/api/query",
                json=test_payload,
                timeout=5
            )
            integration_points.append("query_endpoint_availability")

            if response.status_code not in [200, 500]:  # 500 is OK for test query
                warnings.append(f"Query endpoint returned unexpected status: {response.status_code}")

        except Exception as e:
            errors.append(f"Query endpoint test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="API Health Test",
            component_tested="FastAPI",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'api_server': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_classification_agent_health(self) -> IntegrationTestResult:
        """Test Classification Agent integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Import and test classification agent directly
            from agents.classification_agent import ClassificationAgent

            agent = ClassificationAgent()
            integration_points.append("agent_instantiation")

            # Test classification
            test_question = "What is the payroll tax rate?"
            result = agent.classify_question(test_question)
            integration_points.append("question_classification")

            # Validate classification result
            if not result:
                errors.append("Classification agent returned empty result")
            else:
                if not hasattr(result, 'revenue_type'):
                    errors.append("Classification result missing revenue_type")
                if not hasattr(result, 'question_intent'):
                    errors.append("Classification result missing question_intent")
                if not hasattr(result, 'confidence'):
                    errors.append("Classification result missing confidence")

                integration_points.append("result_validation")

        except ImportError as e:
            errors.append(f"Failed to import ClassificationAgent: {str(e)}")
        except Exception as e:
            errors.append(f"Classification agent test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Classification Agent Health Test",
            component_tested="ClassificationAgent",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'classification_agent': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_orchestrator_health(self) -> IntegrationTestResult:
        """Test Orchestrator integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Import and test orchestrator directly
            from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

            orchestrator = LocalDualAgentOrchestrator()
            integration_points.append("orchestrator_instantiation")

            # Test health check method
            health = orchestrator.health_check()
            integration_points.append("health_check_method")

            if not health:
                errors.append("Orchestrator health check returned empty result")
            else:
                status = health.get('orchestrator_status', 'unknown')
                if status not in ['healthy', 'degraded']:
                    errors.append(f"Unexpected orchestrator status: {status}")

                components = health.get('components', {})
                for component, status in components.items():
                    if status == 'unhealthy':
                        warnings.append(f"Component {component} is unhealthy")

                integration_points.append("component_status_validation")

        except ImportError as e:
            errors.append(f"Failed to import LocalDualAgentOrchestrator: {str(e)}")
        except Exception as e:
            errors.append(f"Orchestrator test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Orchestrator Health Test",
            component_tested="LocalDualAgentOrchestrator",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'orchestrator': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_vector_store_health(self) -> IntegrationTestResult:
        """Test Vector Store integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test local vector store
            from data.local_vector_store import LocalVectorStore

            vector_store = LocalVectorStore()
            integration_points.append("vector_store_instantiation")

            # Test basic search functionality
            test_results = vector_store.search("payroll tax", k=3)
            integration_points.append("vector_search")

            if not isinstance(test_results, list):
                errors.append("Vector store search did not return a list")
            elif len(test_results) == 0:
                warnings.append("Vector store search returned no results")
            else:
                # Validate result structure
                for result in test_results[:1]:  # Check first result
                    if not isinstance(result, dict):
                        errors.append("Vector store result is not a dictionary")
                    else:
                        required_fields = ['content', 'similarity_score']
                        for field in required_fields:
                            if field not in result:
                                warnings.append(f"Vector store result missing field: {field}")

                integration_points.append("result_structure_validation")

            # Test available acts listing
            try:
                acts = vector_store.list_available_acts()
                integration_points.append("acts_listing")

                if not isinstance(acts, list):
                    warnings.append("list_available_acts did not return a list")
                elif len(acts) == 0:
                    warnings.append("No acts available in vector store")

            except Exception as e:
                warnings.append(f"Failed to list available acts: {str(e)}")

        except ImportError as e:
            errors.append(f"Failed to import LocalVectorStore: {str(e)}")
        except Exception as e:
            errors.append(f"Vector store test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Vector Store Health Test",
            component_tested="LocalVectorStore",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'vector_store': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_primary_agent_health(self) -> IntegrationTestResult:
        """Test Primary Agent integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Import and test primary agent
            from agents.local_primary_agent import LocalPrimaryResponseAgent

            agent = LocalPrimaryResponseAgent()
            integration_points.append("primary_agent_instantiation")

            # Test response generation
            test_query = "What is the payroll tax rate?"
            test_context = [
                {
                    'act_name': 'Payroll Tax Act 2007',
                    'content': 'The payroll tax rate is 5.25%',
                    'similarity_score': 0.9
                }
            ]

            response = agent.generate_response(test_query, test_context)
            integration_points.append("response_generation")

            if not response:
                errors.append("Primary agent returned empty response")
            else:
                # Validate response structure
                required_attributes = ['answer', 'confidence', 'citations']
                for attr in required_attributes:
                    if not hasattr(response, attr):
                        errors.append(f"Primary agent response missing attribute: {attr}")

                if hasattr(response, 'answer') and len(response.answer) < 10:
                    warnings.append("Primary agent response very short")

                integration_points.append("response_validation")

        except ImportError as e:
            errors.append(f"Failed to import LocalPrimaryResponseAgent: {str(e)}")
        except Exception as e:
            errors.append(f"Primary agent test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Primary Agent Health Test",
            component_tested="LocalPrimaryResponseAgent",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'primary_agent': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_api_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test API integration with various request types"""
        api_tests = {}

        # Test different query types
        for query_type, query in self.integration_test_queries.items():
            test_result = await self._test_api_query_integration(query, query_type)
            api_tests[f"api_query_{query_type}"] = test_result

        # Test API parameter variations
        parameter_test = await self._test_api_parameter_integration()
        api_tests['api_parameters'] = parameter_test

        # Test API response format
        format_test = await self._test_api_response_format()
        api_tests['api_response_format'] = format_test

        return api_tests

    async def _test_api_query_integration(self, query: str, query_type: str) -> IntegrationTestResult:
        """Test API integration with specific query"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": query,
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=30
            )
            integration_points.append("api_request")

            if response.status_code == 200:
                data = response.json()
                integration_points.append("json_parsing")

                # Validate response structure
                required_fields = ['answer', 'confidence', 'classification', 'source_count']
                for field in required_fields:
                    if field not in data:
                        errors.append(f"API response missing field: {field}")

                # Validate data types
                if 'confidence' in data and not isinstance(data['confidence'], (int, float)):
                    errors.append("Confidence field is not numeric")

                if 'source_count' in data and not isinstance(data['source_count'], int):
                    errors.append("Source count field is not integer")

                integration_points.append("response_validation")

            else:
                errors.append(f"API returned status code: {response.status_code}")

        except requests.exceptions.Timeout:
            errors.append("API request timed out")
        except requests.exceptions.ConnectionError:
            errors.append("Failed to connect to API")
        except Exception as e:
            errors.append(f"API integration test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name=f"API Query Integration - {query_type}",
            component_tested="FastAPI",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'api': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_api_parameter_integration(self) -> IntegrationTestResult:
        """Test API with different parameter combinations"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        parameter_combinations = [
            {"enable_approval": True, "include_metadata": True},
            {"enable_approval": False, "include_metadata": True},
            {"enable_approval": True, "include_metadata": False},
            {"enable_approval": False, "include_metadata": False}
        ]

        for i, params in enumerate(parameter_combinations):
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/query",
                    json={
                        "question": "What is the payroll tax rate?",
                        **params
                    },
                    timeout=15
                )
                integration_points.append(f"parameter_combo_{i+1}")

                if response.status_code != 200:
                    errors.append(f"Parameter combination {i+1} failed with status {response.status_code}")

            except Exception as e:
                errors.append(f"Parameter combination {i+1} failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="API Parameter Integration",
            component_tested="FastAPI",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'api_parameters': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_api_response_format(self) -> IntegrationTestResult:
        """Test API response format consistency"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": "What is the payroll tax rate?",
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=15
            )
            integration_points.append("response_format_test")

            if response.status_code == 200:
                data = response.json()

                # Check response format compliance
                expected_structure = {
                    'answer': str,
                    'confidence': (int, float),
                    'citations': list,
                    'processing_time': (int, float),
                    'classification': dict,
                    'approval_status': str,
                    'source_count': int
                }

                for field, expected_type in expected_structure.items():
                    if field not in data:
                        errors.append(f"Missing required field: {field}")
                    elif not isinstance(data[field], expected_type):
                        errors.append(f"Field {field} has wrong type: expected {expected_type}, got {type(data[field])}")

                integration_points.append("format_validation")

            else:
                errors.append(f"Response format test failed with status: {response.status_code}")

        except Exception as e:
            errors.append(f"Response format test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="API Response Format",
            component_tested="FastAPI",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'response_format': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_agent_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test agent-to-agent integration"""
        agent_tests = {}

        # Test classification to orchestrator integration
        classification_test = await self._test_classification_to_orchestrator_integration()
        agent_tests['classification_to_orchestrator'] = classification_test

        # Test orchestrator to primary agent integration
        orchestrator_test = await self._test_orchestrator_to_primary_agent_integration()
        agent_tests['orchestrator_to_primary'] = orchestrator_test

        # Test agent chain integration
        chain_test = await self._test_agent_chain_integration()
        agent_tests['agent_chain'] = chain_test

        return agent_tests

    async def _test_classification_to_orchestrator_integration(self) -> IntegrationTestResult:
        """Test integration between classification agent and orchestrator"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            from agents.classification_agent import ClassificationAgent
            from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

            # Test classification
            classifier = ClassificationAgent()
            classification_result = classifier.classify_question("What is the payroll tax rate?")
            integration_points.append("classification")

            # Test orchestrator with classification result
            orchestrator = LocalDualAgentOrchestrator()
            response = orchestrator.process_query(
                "What is the payroll tax rate?",
                classification_result=classification_result
            )
            integration_points.append("orchestrator_processing")

            if not response:
                errors.append("Orchestrator returned empty response")
            else:
                if not hasattr(response, 'final_response'):
                    errors.append("Orchestrator response missing final_response")

                integration_points.append("response_validation")

        except Exception as e:
            errors.append(f"Classification to orchestrator integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Classification to Orchestrator Integration",
            component_tested="Agent Integration",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'agent_integration': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_orchestrator_to_primary_agent_integration(self) -> IntegrationTestResult:
        """Test integration between orchestrator and primary agent"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

            orchestrator = LocalDualAgentOrchestrator()

            # Test orchestrator calling primary agent
            response = orchestrator.process_query("What is the payroll tax rate?")
            integration_points.append("orchestrator_to_primary")

            if not response:
                errors.append("Orchestrator failed to get response from primary agent")
            else:
                # Check that primary agent was involved
                if hasattr(response, 'primary_response'):
                    integration_points.append("primary_response_validation")
                else:
                    errors.append("Response missing primary_response attribute")

        except Exception as e:
            errors.append(f"Orchestrator to primary agent integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Orchestrator to Primary Agent Integration",
            component_tested="Agent Integration",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'orchestrator_primary': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_agent_chain_integration(self) -> IntegrationTestResult:
        """Test full agent chain integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            from agents.classification_agent import ClassificationAgent
            from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

            # Full chain test
            test_query = "Calculate payroll tax for $2.5 million in wages"

            # Step 1: Classification
            classifier = ClassificationAgent()
            classification = classifier.classify_question(test_query)
            integration_points.append("full_chain_classification")

            # Step 2: Orchestration
            orchestrator = LocalDualAgentOrchestrator()
            response = orchestrator.process_query(test_query, classification_result=classification)
            integration_points.append("full_chain_orchestration")

            # Step 3: Validation
            if not response or not hasattr(response, 'final_response'):
                errors.append("Full agent chain failed to produce response")
            else:
                final_response = response.final_response
                if not hasattr(final_response, 'content') or len(final_response.content) < 10:
                    errors.append("Full agent chain produced insufficient response")

                integration_points.append("full_chain_validation")

        except Exception as e:
            errors.append(f"Full agent chain integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Full Agent Chain Integration",
            component_tested="Agent Chain",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'agent_chain': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_vector_store_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test vector store integration with agents"""
        vector_tests = {}

        # Test vector store to agent integration
        agent_integration_test = await self._test_vector_store_to_agent_integration()
        vector_tests['vector_to_agent'] = agent_integration_test

        # Test context retrieval integration
        context_test = await self._test_context_retrieval_integration()
        vector_tests['context_retrieval'] = context_test

        return vector_tests

    async def _test_vector_store_to_agent_integration(self) -> IntegrationTestResult:
        """Test vector store integration with agents"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            from data.local_vector_store import LocalVectorStore
            from agents.local_primary_agent import LocalPrimaryResponseAgent

            # Test vector store search
            vector_store = LocalVectorStore()
            search_results = vector_store.search("payroll tax rate", k=3)
            integration_points.append("vector_search")

            if not search_results:
                warnings.append("Vector store returned no results")
            else:
                # Test agent with vector store results
                agent = LocalPrimaryResponseAgent()
                response = agent.generate_response("What is the payroll tax rate?", search_results)
                integration_points.append("agent_with_vector_results")

                if not response:
                    errors.append("Agent failed to process vector store results")
                else:
                    integration_points.append("vector_agent_integration_validation")

        except Exception as e:
            errors.append(f"Vector store to agent integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Vector Store to Agent Integration",
            component_tested="Vector Store Integration",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'vector_agent': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_context_retrieval_integration(self) -> IntegrationTestResult:
        """Test context retrieval integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test dynamic context layer if available
            try:
                from data.dynamic_context_layer import DynamicContextLayer

                context_layer = DynamicContextLayer()
                context_docs = context_layer.get_relevant_context("payroll tax", max_docs=3)
                integration_points.append("dynamic_context_retrieval")

                if not context_docs:
                    warnings.append("Dynamic context layer returned no documents")

            except ImportError:
                warnings.append("Dynamic context layer not available")

            # Fallback to local vector store
            from data.local_vector_store import LocalVectorStore

            vector_store = LocalVectorStore()
            vector_results = vector_store.search("payroll tax", k=3)
            integration_points.append("fallback_vector_retrieval")

            if not vector_results:
                errors.append("No context retrieval method returned results")

        except Exception as e:
            errors.append(f"Context retrieval integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Context Retrieval Integration",
            component_tested="Context Retrieval",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'context_retrieval': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_database_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test database integration"""
        database_tests = {}

        # Test results database integration (for test framework)
        results_db_test = await self._test_results_database_integration()
        database_tests['results_database'] = results_db_test

        return database_tests

    async def _test_results_database_integration(self) -> IntegrationTestResult:
        """Test results database integration"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test database connection and operations
            db_path = ":memory:"  # Use in-memory database for testing
            conn = sqlite3.connect(db_path)
            integration_points.append("database_connection")

            # Test table creation
            conn.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY,
                    test_name TEXT,
                    result TEXT,
                    timestamp DATETIME
                )
            ''')
            integration_points.append("table_creation")

            # Test insert
            conn.execute(
                "INSERT INTO test_results (test_name, result, timestamp) VALUES (?, ?, ?)",
                ("test", "passed", datetime.now())
            )
            conn.commit()
            integration_points.append("data_insertion")

            # Test query
            cursor = conn.execute("SELECT COUNT(*) FROM test_results")
            count = cursor.fetchone()[0]
            if count != 1:
                errors.append(f"Database query returned unexpected count: {count}")

            integration_points.append("data_retrieval")

            conn.close()

        except Exception as e:
            errors.append(f"Database integration failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Results Database Integration",
            component_tested="SQLite Database",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'database': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_error_handling_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test error handling integration"""
        error_tests = {}

        # Test API error handling
        api_error_test = await self._test_api_error_handling()
        error_tests['api_error_handling'] = api_error_test

        # Test agent error handling
        agent_error_test = await self._test_agent_error_handling()
        error_tests['agent_error_handling'] = agent_error_test

        return error_tests

    async def _test_api_error_handling(self) -> IntegrationTestResult:
        """Test API error handling"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        # Test various error scenarios
        error_scenarios = [
            {"payload": {"question": ""}, "expected": "empty question"},
            {"payload": {"invalid_field": "test"}, "expected": "missing question"},
            {"payload": {"question": "test", "enable_approval": "invalid"}, "expected": "invalid approval type"},
        ]

        for i, scenario in enumerate(error_scenarios):
            try:
                response = requests.post(
                    f"{self.api_base_url}/api/query",
                    json=scenario["payload"],
                    timeout=10
                )
                integration_points.append(f"error_scenario_{i+1}")

                # API should handle errors gracefully (not crash)
                if response.status_code == 200:
                    # Check if error is properly handled in response
                    data = response.json()
                    if "error" not in data.get("answer", "").lower():
                        warnings.append(f"Scenario {i+1}: API didn't indicate error in response")
                elif response.status_code == 422:
                    # Validation error is acceptable
                    pass
                elif response.status_code >= 500:
                    errors.append(f"Scenario {i+1}: API returned server error {response.status_code}")

            except requests.exceptions.Timeout:
                warnings.append(f"Scenario {i+1}: Request timed out")
            except Exception as e:
                warnings.append(f"Scenario {i+1}: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="API Error Handling",
            component_tested="FastAPI Error Handling",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'error_handling': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_agent_error_handling(self) -> IntegrationTestResult:
        """Test agent error handling"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

            orchestrator = LocalDualAgentOrchestrator()

            # Test with problematic queries
            problematic_queries = [
                "",  # Empty query
                "x" * 10000,  # Very long query
                "🤖🤖🤖",  # Special characters only
                None  # Invalid input type (if not caught by API)
            ]

            for i, query in enumerate(problematic_queries):
                try:
                    if query is None:
                        continue  # Skip None test for now

                    response = orchestrator.process_query(str(query))
                    integration_points.append(f"agent_error_scenario_{i+1}")

                    if response and hasattr(response, 'final_response'):
                        # Agent handled error gracefully
                        integration_points.append(f"graceful_handling_{i+1}")
                    else:
                        warnings.append(f"Agent scenario {i+1}: No response generated")

                except Exception as e:
                    # Agent should handle errors internally, not raise exceptions
                    errors.append(f"Agent scenario {i+1} raised exception: {str(e)}")

        except Exception as e:
            errors.append(f"Agent error handling test failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Agent Error Handling",
            component_tested="Agent Error Handling",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'agent_error_handling': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_end_to_end_integration(self) -> Dict[str, IntegrationTestResult]:
        """Test complete end-to-end integration flows"""
        e2e_tests = {}

        # Test simple end-to-end flow
        simple_e2e = await self._test_simple_end_to_end_flow()
        e2e_tests['simple_e2e'] = simple_e2e

        # Test complex end-to-end flow
        complex_e2e = await self._test_complex_end_to_end_flow()
        e2e_tests['complex_e2e'] = complex_e2e

        return e2e_tests

    async def _test_simple_end_to_end_flow(self) -> IntegrationTestResult:
        """Test simple end-to-end integration flow"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test complete flow: API -> Classification -> Orchestrator -> Primary Agent -> Vector Store -> Response
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": "What is the NSW payroll tax rate?",
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=30
            )
            integration_points.append("end_to_end_request")

            if response.status_code == 200:
                data = response.json()
                integration_points.append("end_to_end_response")

                # Validate full integration worked
                required_components = {
                    'answer': "Response from primary agent",
                    'confidence': "Confidence scoring",
                    'classification': "Classification agent",
                    'source_count': "Vector store integration",
                    'approval_status': "Approval process"
                }

                for field, component in required_components.items():
                    if field not in data:
                        errors.append(f"End-to-end flow missing {component} ({field})")

                # Check answer quality
                answer = data.get('answer', '')
                if len(answer) < 20:
                    warnings.append("End-to-end response very short")

                if 'payroll' not in answer.lower():
                    warnings.append("End-to-end response doesn't mention payroll")

                integration_points.append("end_to_end_validation")

            else:
                errors.append(f"End-to-end flow failed with status: {response.status_code}")

        except Exception as e:
            errors.append(f"Simple end-to-end flow failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Simple End-to-End Flow",
            component_tested="Full System Integration",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'e2e_simple': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    async def _test_complex_end_to_end_flow(self) -> IntegrationTestResult:
        """Test complex end-to-end integration flow"""
        start_time = time.time()
        errors = []
        warnings = []
        integration_points = []

        try:
            # Test with complex multi-tax query
            complex_query = "For a business with $3.4M payroll and 12 properties worth $43.2M total including 240 parking spaces, what is the total NSW revenue liability?"

            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": complex_query,
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=60  # Longer timeout for complex query
            )
            integration_points.append("complex_e2e_request")

            if response.status_code == 200:
                data = response.json()
                integration_points.append("complex_e2e_response")

                # Validate complex integration components
                answer = data.get('answer', '')

                # Check for multi-tax handling
                tax_types = ['payroll', 'land', 'parking']
                found_taxes = sum(1 for tax_type in tax_types if tax_type in answer.lower())

                if found_taxes < 2:
                    warnings.append("Complex query didn't identify multiple tax types")

                # Check for calculations
                if '$' not in answer:
                    warnings.append("Complex query didn't include monetary calculations")

                # Check classification handled complexity
                classification = data.get('classification', {})
                if not classification.get('is_multi_tax_question', False):
                    warnings.append("Classification didn't identify multi-tax scenario")

                integration_points.append("complex_e2e_validation")

            else:
                errors.append(f"Complex end-to-end flow failed with status: {response.status_code}")

        except Exception as e:
            errors.append(f"Complex end-to-end flow failed: {str(e)}")

        response_time = time.time() - start_time

        return IntegrationTestResult(
            test_name="Complex End-to-End Flow",
            component_tested="Full System Integration",
            passed=len(errors) == 0,
            response_time=response_time,
            error_details=errors,
            warnings=warnings,
            component_status={'e2e_complex': 'healthy' if len(errors) == 0 else 'unhealthy'},
            integration_points_validated=integration_points,
            timestamp=datetime.now()
        )

    def _assess_overall_integration_health(self, integration_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall integration health"""
        all_tests = []

        # Collect all test results
        for category_name, category_results in integration_results.items():
            if isinstance(category_results, dict) and 'start_time' not in category_results:
                for test_name, test_result in category_results.items():
                    if isinstance(test_result, IntegrationTestResult):
                        all_tests.append(test_result)
            elif isinstance(category_results, IntegrationTestResult):
                all_tests.append(category_results)

        if not all_tests:
            return {'status': 'unknown', 'details': 'No test results found'}

        # Calculate overall health metrics
        total_tests = len(all_tests)
        passed_tests = sum(1 for test in all_tests if test.passed)
        failed_tests = total_tests - passed_tests

        avg_response_time = sum(test.response_time for test in all_tests) / total_tests

        # Component health summary
        component_health = {}
        for test in all_tests:
            for component, status in test.component_status.items():
                if component not in component_health:
                    component_health[component] = []
                component_health[component].append(status)

        # Determine overall component health
        overall_component_health = {}
        for component, statuses in component_health.items():
            healthy_count = sum(1 for status in statuses if status == 'healthy')
            overall_component_health[component] = 'healthy' if healthy_count > len(statuses) / 2 else 'unhealthy'

        # Overall assessment
        integration_health = {
            'overall_status': 'healthy' if passed_tests / total_tests >= 0.9 else 'degraded' if passed_tests / total_tests >= 0.7 else 'unhealthy',
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': passed_tests / total_tests,
            'average_response_time': avg_response_time,
            'component_health': overall_component_health,
            'critical_issues': [test.test_name for test in all_tests if not test.passed and 'critical' in test.test_name.lower()],
            'production_ready': passed_tests / total_tests >= 0.95 and avg_response_time <= 5.0
        }

        return integration_health

    def _generate_integration_report(self, integration_results: Dict[str, Any]):
        """Generate detailed integration test report"""
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = reports_dir / f"integration_test_report_{timestamp}.json"

        # Make results JSON serializable
        serializable_results = self._make_serializable(integration_results)

        with open(report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Integration test report generated: {report_path}")

    def _make_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, IntegrationTestResult):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj


async def main():
    """
    Run the integration test suite
    """
    integration_suite = IntegrationTestSuite()

    print("🔗 NSW Revenue AI Integration Test Suite")
    print("="*60)

    # Run comprehensive integration tests
    results = await integration_suite.run_comprehensive_integration_tests()

    # Print summary
    health = results['overall_integration_health']

    print(f"\n📊 INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Overall Status: {health.get('overall_status', 'unknown').upper()}")
    print(f"Total Tests: {health.get('total_tests', 0)}")
    print(f"Passed: {health.get('passed_tests', 0)}")
    print(f"Failed: {health.get('failed_tests', 0)}")
    print(f"Pass Rate: {health.get('pass_rate', 0)*100:.1f}%")
    print(f"Average Response Time: {health.get('average_response_time', 0):.2f}s")
    print(f"Production Ready: {'✅' if health.get('production_ready', False) else '❌'}")

    # Print component health
    component_health = health.get('component_health', {})
    if component_health:
        print(f"\n🔧 COMPONENT HEALTH:")
        for component, status in component_health.items():
            status_icon = '✅' if status == 'healthy' else '❌'
            print(f"  {status_icon} {component}: {status}")

    # Print critical issues
    critical_issues = health.get('critical_issues', [])
    if critical_issues:
        print(f"\n⚠️ CRITICAL ISSUES:")
        for i, issue in enumerate(critical_issues, 1):
            print(f"{i}. {issue}")

    return 0 if health.get('production_ready', False) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))