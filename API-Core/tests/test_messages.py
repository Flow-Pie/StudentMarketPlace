import pytest
from flask import url_for
from flask_jwt_extended import create_access_token

@pytest.fixture
def auth_headers(user):
    token = create_access_token(identity=user.user_id)
    return {
        'Authorization': f'Bearer {token}'
    }

def test_get_inbox_messages(client, auth_headers):
    user_id = 1  
    response = client.get(f'/api/messages/{user_id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        message = data[0]
        assert 'message_id' in message
        assert 'conversation_id' in message
        assert 'sender_id' in message
        assert 'receiver_id' in message
        assert 'content' in message
        assert 'sent_at' in message
