"""
This file contains integration tests for methods in the :py:class:`Synapse` class that act as helpers for making REST
requests to the Synapse backend
"""


from nose.tools import assert_in, assert_dict_contains_subset, assert_equals

from synapseclient import *
from tests import integration


def setup(module):
    module.syn = integration.syn


def test_createColumns():
    columns_to_create = [Column(name="FirstTestColumn", columnType="INTEGER"), Column(name="SecondTestColumn",
                                                                                      columnType="DOUBLE")]
    created_columns = syn.createColumns(columns_to_create)
    assert_equals(len(columns_to_create), len(created_columns))
    for col_to_create, created_col in zip(columns_to_create, created_columns):
        assert_in('id', created_col)
        assert_dict_contains_subset(col_to_create, created_col)
