#!/usr/bin/env python3
"""
NSW Revenue AI Assistant - Command Line Interface
Direct terminal interaction without web server complexity
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.classification_agent import ClassificationAgent
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NSWRevenueCLI:
    """NSW Revenue AI Assistant Command Line Interface"""

    def __init__(self):
        print("🏛️  NSW Revenue AI Assistant - CLI Mode")
        print("=" * 50)

        try:
            self.classification_agent = ClassificationAgent()
            self.orchestrator = LocalDualAgentOrchestrator()
            print("✅ All agents initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing agents: {e}")
            sys.exit(1)

    def process_query(self, question: str):
        """Process a single query through the full pipeline"""
        print(f"\n🔍 Processing: '{question}'")
        print("-" * 50)

        try:
            # Step 1: Classification
            print("📋 Step 1: Classifying question...")
            classification_result = self.classification_agent.classify_question(question)

            print(f"   Revenue Type: {classification_result.revenue_type.value}")
            print(f"   Intent: {classification_result.question_intent.value}")
            print(f"   Confidence: {classification_result.confidence:.2f}")
            print(f"   Simple Calculation: {classification_result.is_simple_calculation}")

            # Step 2: Full Processing
            print("\n🤖 Step 2: Processing through dual agent system...")
            start_time = datetime.now()

            response = self.orchestrator.process_query(
                question,
                enable_approval=True,
                include_metadata=True,
                classification_result=classification_result
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # Step 3: Display Results
            print(f"\n📊 Processing completed in {processing_time:.2f}s")
            print(f"   Primary Confidence: {response.primary_response.confidence:.2f}")
            print(f"   Final Confidence: {response.final_response.confidence_score:.2f}")
            print(f"   Approval Status: {'✅ Approved' if response.approval_decision.is_approved else '⚠️  Pending Review'}")

            print(f"\n💬 **ANSWER:**")
            print(response.final_response.content)

            if response.final_response.citations:
                print(f"\n📚 **CITATIONS:**")
                for i, citation in enumerate(response.final_response.citations, 1):
                    print(f"   {i}. {citation}")

            if response.final_response.source_documents:
                print(f"\n📄 **SOURCES:** {len(response.final_response.source_documents)} documents")
                for i, doc in enumerate(response.final_response.source_documents[:3], 1):
                    print(f"   {i}. {doc.get('act_name', 'Unknown')} (Score: {doc.get('similarity_score', 0):.2f})")

            if response.approval_decision.review_notes:
                print(f"\n📝 **REVIEW NOTES:**")
                for note in response.approval_decision.review_notes:
                    print(f"   • {note}")

            return response

        except Exception as e:
            print(f"❌ Error processing query: {e}")
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return None

    def run_interactive(self):
        """Run interactive chat session"""
        print("\n🎯 Interactive Mode - Enter NSW Revenue questions")
        print("Commands: 'quit', 'exit', 'help', 'test'")
        print("=" * 50)

        while True:
            try:
                question = input("\n💡 Your Question: ").strip()

                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                elif question.lower() == 'help':
                    self.show_help()
                    continue

                elif question.lower() == 'test':
                    self.run_test_queries()
                    continue

                elif not question:
                    print("Please enter a question.")
                    continue

                self.process_query(question)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def show_help(self):
        """Display help information"""
        print("\n📖 **NSW Revenue AI Assistant Help**")
        print("=" * 40)
        print("This assistant can answer questions about:")
        print("• Payroll Tax rates and calculations")
        print("• Land Tax exemptions and thresholds")
        print("• Stamp Duty concessions and rates")
        print("• Revenue administration processes")
        print("• Penalties and compliance requirements")
        print("\n📝 **Example Questions:**")
        print("• What is the payroll tax rate in NSW?")
        print("• How do I calculate land tax for 3 properties?")
        print("• What stamp duty concessions are available for first home buyers?")
        print("• What are the penalties for late payroll tax payment?")

    def run_test_queries(self):
        """Run a set of test queries"""
        test_questions = [
            "What is the current payroll tax rate in NSW?",
            "How do I calculate land tax for residential property?",
            "What stamp duty concessions are available for first home buyers?",
            "What are the penalties for late payroll tax payment?"
        ]

        print("\n🧪 **Running Test Queries**")
        print("=" * 40)

        for i, question in enumerate(test_questions, 1):
            print(f"\n🔬 Test {i}/{len(test_questions)}")
            response = self.process_query(question)

            if response:
                print("✅ Test passed")
            else:
                print("❌ Test failed")

def main():
    """Main entry point"""
    cli = NSWRevenueCLI()

    if len(sys.argv) > 1:
        # Single query mode
        question = " ".join(sys.argv[1:])
        cli.process_query(question)
    else:
        # Interactive mode
        cli.run_interactive()

if __name__ == "__main__":
    main()