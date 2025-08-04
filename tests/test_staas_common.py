import pytest
from unittest.mock import MagicMock
from staas_common import list_fleets, list_members

class DummyClient:
    def get_fleets(self):
        class Response:
            status_code = 200
            items = [type('Fleet', (), {'name': 'fleet1'})()]
        return Response()
    def get_fleets_members(self):
        class Member:
            member = type('Member', (), {'name': 'array1'})()
        class Response:
            status_code = 200
            items = [Member()]
        return Response()

def test_list_fleets():
    client = DummyClient()
    fleets = list_fleets(client)
    assert fleets == ['fleet1']

def test_list_members():
    client = DummyClient()
    members = list_members(client, ['fleet1'])
    assert members == ['array1']
