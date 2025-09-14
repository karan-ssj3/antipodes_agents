import unittest
import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.workflow import AgentWorkflow

class TestFullSystem(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow execution"""
        workflow = AgentWorkflow()
        
        # Run with known good date
        try:
            final_state = workflow.run(date(2025, 7, 1))
            
            # Verify all expected outputs exist
            self.assertIn("coordinator_results", final_state)
            self.assertIn("backtest_result", final_state)
            self.assertIn("output_files", final_state)
            
            # Verify coordinator results
            results = final_state["coordinator_results"]
            self.assertEqual(len(results), 4)  # One per ticker
            
            # Verify backtest result
            backtest = final_state["backtest_result"]
            self.assertIsNotNone(backtest.portfolio_return)
            self.assertIsNotNone(backtest.benchmark_return)
            
            # Verify output files were created
            files = final_state["output_files"]
            self.assertIn("picks", files)
            self.assertIn("performance", files)
            self.assertIn("chart", files)
            
        except Exception as e:
            self.fail(f"End-to-end workflow failed: {e}")

if __name__ == "__main__":
    unittest.main()