"""
Tests for HTN Service

Tests the HtnService class including edge cases like:
- Queries that return 0 solutions
- Queries that return multiple solutions
- Invalid queries
- Malformed data from C++
"""

import sys
import os
import unittest
import json

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../gui/backend')))

from htn_service import HtnService


class TestHtnServiceBasic(unittest.TestCase):
    """Basic tests for HtnService"""

    def setUp(self):
        self.service = HtnService()

    def test_load_valid_file(self):
        """Test loading a valid HTN file"""
        success, error = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success, f"Failed to load Taxi.htn: {error}")
        self.assertIsNone(error)

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist"""
        success, error = self.service.load_file('Examples/NonExistent.htn')
        self.assertFalse(success)
        self.assertIn("not found", error.lower())

    def test_get_state_facts(self):
        """Test getting state facts after loading a file"""
        success, _ = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success)

        facts = self.service.get_state_facts()
        self.assertIsInstance(facts, list)
        self.assertGreater(len(facts), 0)


class TestHtnQueryWithSolutions(unittest.TestCase):
    """Tests for HTN queries that return solutions"""

    def setUp(self):
        self.service = HtnService()
        success, error = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success, f"Failed to load Taxi.htn: {error}")

    def test_query_with_solutions(self):
        """Test a query that returns solutions"""
        result = self.service.execute_htn_query('travel-to(park).', enhanced_trace=True)

        self.assertNotIn('error', result)
        self.assertIn('solutions', result)
        self.assertIn('trees', result)
        self.assertIn('total_count', result)
        self.assertGreater(result['total_count'], 0)

    def test_query_trees_structure(self):
        """Test that returned trees have correct structure"""
        result = self.service.execute_htn_query('travel-to(park).', enhanced_trace=True)

        self.assertGreater(len(result['trees']), 0)

        tree = result['trees'][0]
        self.assertIn('id', tree)
        self.assertIn('name', tree)
        self.assertIn('status', tree)
        self.assertIn('children', tree)

    def test_query_without_enhanced_trace(self):
        """Test query without enhanced trace analysis"""
        result = self.service.execute_htn_query('travel-to(park).', enhanced_trace=False)

        self.assertNotIn('error', result)
        self.assertGreater(result['total_count'], 0)


class TestHtnQueryNoSolutions(unittest.TestCase):
    """Tests for HTN queries that return 0 solutions"""

    def setUp(self):
        self.service = HtnService()
        success, error = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success, f"Failed to load Taxi.htn: {error}")

    def test_query_no_solutions_returns_empty(self):
        """Test that a query with no solutions returns empty lists, not an error"""
        result = self.service.execute_htn_query('travel-to(mars).', enhanced_trace=True)

        # Should NOT have an error key with a message
        if 'error' in result:
            self.fail(f"Query returned error instead of empty result: {result['error']}")

        self.assertIn('solutions', result)
        self.assertIn('trees', result)
        self.assertIn('total_count', result)
        self.assertEqual(result['total_count'], 0)
        self.assertEqual(len(result['solutions']), 0)
        self.assertEqual(len(result['trees']), 0)

    def test_query_no_solutions_without_enhanced_trace(self):
        """Test query with no solutions without enhanced trace"""
        result = self.service.execute_htn_query('travel-to(mars).', enhanced_trace=False)

        if 'error' in result:
            self.fail(f"Query returned error: {result['error']}")

        self.assertEqual(result['total_count'], 0)

    def test_query_impossible_goal(self):
        """Test various impossible goals"""
        impossible_goals = [
            'travel-to(nonexistent).',
            'travel-to(xyz123).',
        ]

        for goal in impossible_goals:
            with self.subTest(goal=goal):
                result = self.service.execute_htn_query(goal, enhanced_trace=True)

                if 'error' in result:
                    self.fail(f"Goal '{goal}' returned error: {result['error']}")

                self.assertEqual(result['total_count'], 0,
                    f"Goal '{goal}' should have 0 solutions")


class TestHtnQueryInvalidSyntax(unittest.TestCase):
    """Tests for HTN queries with invalid syntax"""

    def setUp(self):
        self.service = HtnService()
        success, error = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success, f"Failed to load Taxi.htn: {error}")

    def test_malformed_query_missing_period(self):
        """Test query missing terminal period"""
        result = self.service.execute_htn_query('travel-to(park)', enhanced_trace=True)
        # This may or may not be an error depending on parser tolerance
        # Just ensure it doesn't crash
        self.assertIsInstance(result, dict)

    def test_empty_query(self):
        """Test empty query string"""
        result = self.service.execute_htn_query('', enhanced_trace=True)
        self.assertIsInstance(result, dict)

    def test_query_undefined_predicate(self):
        """Test query with undefined predicate"""
        result = self.service.execute_htn_query('undefined_predicate(x).', enhanced_trace=True)
        self.assertIsInstance(result, dict)


class TestTreeTransformation(unittest.TestCase):
    """Tests for tree transformation logic"""

    def setUp(self):
        self.service = HtnService()

    def test_transform_empty_nodes(self):
        """Test transformation of empty node list"""
        result = self.service._transform_decomp_tree([], 0)
        self.assertIsNone(result)

    def test_transform_none_nodes(self):
        """Test transformation of None"""
        result = self.service._transform_decomp_tree(None, 0)
        self.assertIsNone(result)

    def test_transform_single_node(self):
        """Test transformation of single node"""
        nodes = [{
            'nodeID': 0,
            'parentNodeID': -1,
            'childNodeIDs': [],
            'taskName': 'goal()',
            'methodSignature': 'goal()',
            'isOperator': False,
            'isSuccess': True,
            'isFailed': False,
            'unifiers': [],
            'conditionBindings': [],
            'conditionTerms': []
        }]

        result = self.service._transform_decomp_tree(nodes, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'goal')
        self.assertEqual(result['status'], 'success')

    def test_transform_with_string_unifiers(self):
        """Test transformation handles string unifiers gracefully"""
        nodes = [{
            'nodeID': 0,
            'parentNodeID': -1,
            'childNodeIDs': [],
            'taskName': 'goal()',
            'methodSignature': 'goal()',
            'isOperator': False,
            'isSuccess': True,
            'isFailed': False,
            'unifiers': ['some_string', {'?x': 'value'}],  # Mix of string and dict
            'conditionBindings': ['another_string'],
            'conditionTerms': []
        }]

        result = self.service._transform_decomp_tree(nodes, 0)

        self.assertIsNotNone(result)
        # Should not crash, and should extract dict bindings
        self.assertEqual(result['bindings'], {'?x': 'value'})

    def test_transform_with_parent_child(self):
        """Test transformation with parent-child relationship"""
        nodes = [
            {
                'nodeID': 0,
                'parentNodeID': -1,
                'childNodeIDs': [1],
                'taskName': 'parent()',
                'methodSignature': 'parent()',
                'isOperator': False,
                'isSuccess': True,
                'isFailed': False,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': []
            },
            {
                'nodeID': 1,
                'parentNodeID': 0,
                'childNodeIDs': [],
                'taskName': 'child()',
                'operatorSignature': 'child()',
                'isOperator': True,
                'isSuccess': True,
                'isFailed': False,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': []
            }
        ]

        result = self.service._transform_decomp_tree(nodes, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'parent')
        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['children'][0]['name'], 'child')
        self.assertTrue(result['children'][0]['isOperator'])


class TestSolutionFacts(unittest.TestCase):
    """Tests for solution facts retrieval"""

    def setUp(self):
        self.service = HtnService()
        success, _ = self.service.load_file('Examples/Taxi.htn')
        self.assertTrue(success)

    def test_get_solution_facts_valid_index(self):
        """Test getting facts for a valid solution index"""
        # First execute a query to have solutions
        result = self.service.execute_htn_query('travel-to(park).', enhanced_trace=False)

        if result['total_count'] > 0:
            facts = self.service.get_solution_facts(0)
            self.assertIsInstance(facts, list)

    def test_get_solution_facts_invalid_index(self):
        """Test getting facts for invalid solution index returns empty"""
        facts = self.service.get_solution_facts(9999)
        self.assertIsInstance(facts, list)
        # Should return empty list, not crash

    def test_get_facts_diff(self):
        """Test getting facts diff between initial and solution state"""
        result = self.service.execute_htn_query('travel-to(park).', enhanced_trace=False)

        if result['total_count'] > 0:
            diff = self.service.get_facts_diff(0)
            self.assertIn('added', diff)
            self.assertIn('removed', diff)
            self.assertIn('unchanged', diff)


if __name__ == '__main__':
    unittest.main()
