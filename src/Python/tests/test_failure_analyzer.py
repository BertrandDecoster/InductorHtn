"""
Tests for HTN Failure Analyzer

Tests the failure analysis module that provides detailed failure information
for HTN planning traces.
"""

import sys
import os
import unittest

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../gui/backend')))

from failure_analyzer import (
    FailureCategory,
    FailureDetail,
    AlternativeAttempt,
    EnhancedNode,
    FailureAnalyzer,
    analyze_planning_trace,
    categorize_failure_reason
)


class TestFailureCategory(unittest.TestCase):
    """Tests for FailureCategory enum"""

    def test_all_categories_exist(self):
        """Test that all expected categories are defined"""
        expected = [
            'NO_MATCHING_METHOD',
            'PRECONDITION_FAILED',
            'UNIFICATION_FAILED',
            'SUBTASK_FAILED',
            'OPERATOR_FAILED',
            'NO_SOLUTION',
            'BACKTRACKED',
            'UNKNOWN'
        ]
        for cat_name in expected:
            self.assertTrue(hasattr(FailureCategory, cat_name))


class TestFailureDetail(unittest.TestCase):
    """Tests for FailureDetail dataclass"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        detail = FailureDetail(
            category=FailureCategory.PRECONDITION_FAILED,
            message="Condition not satisfied",
            details={'conditions': ['at(?x)']},
            suggestions=["Add at fact"]
        )

        result = detail.to_dict()

        self.assertEqual(result['category'], 'PRECONDITION_FAILED')
        self.assertEqual(result['message'], "Condition not satisfied")
        self.assertEqual(result['details']['conditions'], ['at(?x)'])
        self.assertEqual(result['suggestions'], ["Add at fact"])

    def test_default_fields(self):
        """Test that default fields are empty"""
        detail = FailureDetail(
            category=FailureCategory.UNKNOWN,
            message="Test"
        )

        self.assertEqual(detail.details, {})
        self.assertEqual(detail.suggestions, [])


class TestAlternativeAttempt(unittest.TestCase):
    """Tests for AlternativeAttempt dataclass"""

    def test_to_dict_success(self):
        """Test successful alternative conversion"""
        alt = AlternativeAttempt(
            method_name="travel",
            signature="travel(?x)",
            success=True,
            failure_reason=None
        )

        result = alt.to_dict()

        self.assertEqual(result['method_name'], 'travel')
        self.assertEqual(result['signature'], 'travel(?x)')
        self.assertTrue(result['success'])
        self.assertIsNone(result['failure_reason'])

    def test_to_dict_failure(self):
        """Test failed alternative conversion"""
        alt = AlternativeAttempt(
            method_name="walk",
            signature="walk(?from, ?to)",
            success=False,
            failure_reason="No path available"
        )

        result = alt.to_dict()

        self.assertFalse(result['success'])
        self.assertEqual(result['failure_reason'], "No path available")


class TestEnhancedNode(unittest.TestCase):
    """Tests for EnhancedNode dataclass"""

    def test_to_dict_basic(self):
        """Test basic node conversion"""
        node = EnhancedNode(
            id='sol0-node1',
            name='travel',
            full_signature='travel(park)',
            task_name='travel(park)',
            is_operator=False,
            status='success',
            bindings={'?dest': 'park'},
            condition_bindings={},
            condition_terms=[],
            children=[]
        )

        result = node.to_dict()

        self.assertEqual(result['id'], 'sol0-node1')
        self.assertEqual(result['name'], 'travel')
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['bindings'], {'?dest': 'park'})
        self.assertIsNone(result['failureDetail'])

    def test_to_dict_with_failure(self):
        """Test node with failure detail"""
        node = EnhancedNode(
            id='sol0-node2',
            name='walk',
            full_signature='walk(home, park)',
            task_name='walk(home, park)',
            is_operator=True,
            status='failure',
            bindings={},
            condition_bindings={},
            condition_terms=['at(home)'],
            children=[],
            failure_detail=FailureDetail(
                category=FailureCategory.PRECONDITION_FAILED,
                message="Missing at(home)"
            ),
            missing_facts=['at(home)'],
            failed_conditions=['at(home)']
        )

        result = node.to_dict()

        self.assertEqual(result['status'], 'failure')
        self.assertIsNotNone(result['failureDetail'])
        self.assertEqual(result['failureDetail']['category'], 'PRECONDITION_FAILED')
        self.assertEqual(result['missingFacts'], ['at(home)'])
        self.assertEqual(result['failedConditions'], ['at(home)'])
        # Legacy compatibility
        self.assertEqual(result['failureReason'], "Missing at(home)")

    def test_to_dict_with_children(self):
        """Test node with children"""
        child = EnhancedNode(
            id='sol0-node2',
            name='walk',
            full_signature='walk(home, park)',
            task_name='walk(home, park)',
            is_operator=True,
            status='success',
            bindings={},
            condition_bindings={},
            condition_terms=[],
            children=[]
        )

        parent = EnhancedNode(
            id='sol0-node1',
            name='travel',
            full_signature='travel(park)',
            task_name='travel(park)',
            is_operator=False,
            status='success',
            bindings={},
            condition_bindings={},
            condition_terms=[],
            children=[child]
        )

        result = parent.to_dict()

        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['children'][0]['name'], 'walk')


class TestCategorizeFailureReason(unittest.TestCase):
    """Tests for the categorize_failure_reason function"""

    def test_no_matching_method(self):
        """Test categorization of no matching method"""
        self.assertEqual(categorize_failure_reason("No method found"), 'NO_MATCHING_METHOD')
        self.assertEqual(categorize_failure_reason("no matching rule"), 'NO_MATCHING_METHOD')

    def test_precondition_failed(self):
        """Test categorization of precondition failure"""
        self.assertEqual(categorize_failure_reason("Precondition not met"), 'PRECONDITION_FAILED')
        self.assertEqual(categorize_failure_reason("condition failed"), 'PRECONDITION_FAILED')

    def test_unification_failed(self):
        """Test categorization of unification failure"""
        self.assertEqual(categorize_failure_reason("Unification error"), 'UNIFICATION_FAILED')
        self.assertEqual(categorize_failure_reason("arity mismatch"), 'UNIFICATION_FAILED')

    def test_subtask_failed(self):
        """Test categorization of subtask failure"""
        self.assertEqual(categorize_failure_reason("Subtask could not complete"), 'SUBTASK_FAILED')
        self.assertEqual(categorize_failure_reason("child task failed"), 'SUBTASK_FAILED')

    def test_operator_failed(self):
        """Test categorization of operator failure"""
        self.assertEqual(categorize_failure_reason("Operator error"), 'OPERATOR_FAILED')

    def test_backtracked(self):
        """Test categorization of backtracking"""
        self.assertEqual(categorize_failure_reason("backtracked from branch"), 'BACKTRACKED')

    def test_unknown(self):
        """Test categorization of unknown failure"""
        self.assertEqual(categorize_failure_reason("Something went wrong"), 'UNKNOWN')
        self.assertEqual(categorize_failure_reason(""), 'UNKNOWN')
        self.assertEqual(categorize_failure_reason(None), 'UNKNOWN')


class TestFailureAnalyzer(unittest.TestCase):
    """Tests for FailureAnalyzer class"""

    def setUp(self):
        self.analyzer = FailureAnalyzer()

    def test_analyze_empty_trace(self):
        """Test analysis of empty trace"""
        result = self.analyzer.analyze_trace([], 0)
        self.assertIsNone(result)

    def test_analyze_single_node_success(self):
        """Test analysis of single successful node"""
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

        result = self.analyzer.analyze_trace(nodes, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'goal')
        self.assertEqual(result.status, 'success')
        self.assertIsNone(result.failure_detail)

    def test_analyze_single_node_failure(self):
        """Test analysis of single failed node"""
        nodes = [{
            'nodeID': 0,
            'parentNodeID': -1,
            'childNodeIDs': [],
            'taskName': 'travel(park)',
            'methodSignature': 'travel(park)',
            'isOperator': False,
            'isSuccess': False,
            'isFailed': True,
            'unifiers': [],
            'conditionBindings': [],
            'conditionTerms': ['at(?x)'],
            'failureReason': 'Precondition failed'
        }]

        result = self.analyzer.analyze_trace(nodes, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'failure')
        self.assertIsNotNone(result.failure_detail)
        self.assertEqual(result.failure_detail.category, FailureCategory.PRECONDITION_FAILED)

    def test_analyze_tree_with_children(self):
        """Test analysis of tree with parent-child relationship"""
        nodes = [
            {
                'nodeID': 0,
                'parentNodeID': -1,
                'childNodeIDs': [1],
                'taskName': 'travel(park)',
                'methodSignature': 'travel(park)',
                'isOperator': False,
                'isSuccess': True,
                'isFailed': False,
                'unifiers': [{'?dest': 'park'}],
                'conditionBindings': [],
                'conditionTerms': []
            },
            {
                'nodeID': 1,
                'parentNodeID': 0,
                'childNodeIDs': [],
                'taskName': 'walk(home, park)',
                'operatorSignature': 'walk(home, park)',
                'isOperator': True,
                'isSuccess': True,
                'isFailed': False,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': []
            }
        ]

        result = self.analyzer.analyze_trace(nodes, 0)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'travel')
        self.assertEqual(len(result.children), 1)
        self.assertEqual(result.children[0].name, 'walk')
        self.assertTrue(result.children[0].is_operator)

    def test_analyze_with_initial_facts(self):
        """Test analysis with initial facts for missing fact detection"""
        nodes = [{
            'nodeID': 0,
            'parentNodeID': -1,
            'childNodeIDs': [],
            'taskName': 'travel(park)',
            'methodSignature': 'travel(park)',
            'isOperator': False,
            'isSuccess': False,
            'isFailed': True,
            'unifiers': [],
            'conditionBindings': [],
            'conditionTerms': ['at(home)', 'hasTicket(park)'],
            'failureReason': 'Precondition failed'
        }]

        initial_facts = ['at(home)', 'money(100)']
        result = self.analyzer.analyze_trace(nodes, 0, initial_facts)

        self.assertIsNotNone(result)
        # at(home) exists in facts, hasTicket does not
        self.assertIn('hasTicket(park)', result.missing_facts)

    def test_subtask_failure_detection(self):
        """Test detection of subtask failure"""
        nodes = [
            {
                'nodeID': 0,
                'parentNodeID': -1,
                'childNodeIDs': [1],
                'taskName': 'travel(park)',
                'methodSignature': 'travel(park)',
                'isOperator': False,
                'isSuccess': False,
                'isFailed': True,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': [],
                'failureReason': ''
            },
            {
                'nodeID': 1,
                'parentNodeID': 0,
                'childNodeIDs': [],
                'taskName': 'walk(home, park)',
                'operatorSignature': 'walk(home, park)',
                'isOperator': True,
                'isSuccess': False,
                'isFailed': True,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': [],
                'failureReason': 'Operator failed'
            }
        ]

        result = self.analyzer.analyze_trace(nodes, 0)

        # Parent should detect that child failed
        self.assertEqual(result.failure_detail.category, FailureCategory.SUBTASK_FAILED)

    def test_alternative_tracking(self):
        """Test tracking of alternative methods tried"""
        nodes = [
            {
                'nodeID': 0,
                'parentNodeID': -1,
                'childNodeIDs': [],
                'taskName': 'travel(park)',
                'methodSignature': 'travel-by-car(park)',
                'isOperator': False,
                'isSuccess': True,
                'isFailed': False,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': []
            },
            {
                'nodeID': 1,
                'parentNodeID': -1,
                'childNodeIDs': [],
                'taskName': 'travel(park)',
                'methodSignature': 'travel-by-bus(park)',
                'isOperator': False,
                'isSuccess': False,
                'isFailed': True,
                'unifiers': [],
                'conditionBindings': [],
                'conditionTerms': [],
                'failureReason': 'No bus available'
            }
        ]

        result = self.analyzer.analyze_trace(nodes, 0)

        # The successful node should have alternatives_tried populated
        self.assertTrue(len(result.alternatives_tried) > 0)


class TestAnalyzePlanningTrace(unittest.TestCase):
    """Tests for the analyze_planning_trace convenience function"""

    def test_returns_dict(self):
        """Test that function returns a dictionary"""
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

        result = analyze_planning_trace(nodes, 0)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'goal')
        self.assertEqual(result['status'], 'success')

    def test_returns_none_for_empty(self):
        """Test that function returns None for empty trace"""
        result = analyze_planning_trace([], 0)
        self.assertIsNone(result)


class TestBuiltinPredicateDetection(unittest.TestCase):
    """Tests for built-in predicate detection"""

    def setUp(self):
        self.analyzer = FailureAnalyzer()

    def test_builtin_predicates_ignored(self):
        """Test that built-in predicates are not reported as missing"""
        nodes = [{
            'nodeID': 0,
            'parentNodeID': -1,
            'childNodeIDs': [],
            'taskName': 'check()',
            'methodSignature': 'check()',
            'isOperator': False,
            'isSuccess': False,
            'isFailed': True,
            'unifiers': [],
            'conditionBindings': [],
            'conditionTerms': ['=(?x, 5)', 'not(at(park))', 'customFact(?y)'],
            'failureReason': 'Precondition failed'
        }]

        result = self.analyzer.analyze_trace(nodes, 0, [])

        # Only customFact should be reported as missing, not = or not
        self.assertIn('customFact(?y)', result.missing_facts)
        # Built-ins should not be in missing facts
        for fact in result.missing_facts:
            self.assertNotIn('=', fact.split('(')[0])
            self.assertNotIn('not', fact.split('(')[0])


if __name__ == '__main__':
    unittest.main()
