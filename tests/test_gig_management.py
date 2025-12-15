import pytest
from app import create_app
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.professional import Professional
from app.models.job import Job, GigInterest, JobStatus
from unittest.mock import patch
import bcrypt

@pytest.fixture(scope='module')
def test_client():
    app, _ = create_app()
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        with app.test_client() as testing_client:
            yield testing_client
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='function')
def init_database(test_client):
    db = SessionLocal()
    # Create users
    hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    institution_user = User(email='institution@test.com', password=hashed_password, role=UserRole.INSTITUTION)
    professional_user = User(email='professional@test.com', password=hashed_password, role=UserRole.PROFESSIONAL)
    db.add(institution_user)
    db.add(professional_user)
    db.commit()

    # Create profiles
    institution = Institution(user_id=institution_user.id, institution_name='Test Inc.')
    professional = Professional(user_id=professional_user.id, full_name='John Doe')
    db.add(institution)
    db.add(professional)
    db.commit()

    # Create a gig
    gig = Job(institution_id=institution.id, title='Test Gig', description='A gig for testing.', pay_amount=100, location='Test Location')
    db.add(gig)
    db.commit()
    db.close()

    yield

    db = SessionLocal()
    db.query(GigInterest).delete()
    db.query(Job).delete()
    db.query(Institution).delete()
    db.query(Professional).delete()
    db.query(User).delete()
    db.commit()
    db.close()

def get_auth_token(client, email, password):
    response = client.post('/api/auth/login', json={'email': email, 'password': password})
    data = response.get_json()
    if 'token' in data:
        return data['token']
    elif 'access_token' in data:
        return data['access_token']
    else:
        raise Exception(f"Login failed: {data}")

@patch('app.socketio')
def test_institution_close_gig(mock_socketio, test_client, init_database):
    institution_token = get_auth_token(test_client, 'institution@test.com', 'password')
    db = SessionLocal()
    gig = db.query(Job).first()
    db.close()

    response = test_client.post(f'/api/jobs/{gig.id}/close', headers={'Authorization': f'Bearer {institution_token}'})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Gig closed successfully'
    db = SessionLocal()
    assert db.query(Job).first().status == JobStatus.CLOSED
    db.close()
    mock_socketio.emit.assert_called_with('gig_update', {'gig_id': gig.id, 'status': 'closed'}, room=f'institution_{gig.institution_id}')

@patch('app.socketio')
def test_professional_cancel_interest(mock_socketio, test_client, init_database):
    professional_token = get_auth_token(test_client, 'professional@test.com', 'password')
    db = SessionLocal()
    professional = db.query(Professional).filter_by(full_name='John Doe').first()
    gig = db.query(Job).first()
    gig_id = gig.id
    institution_user_id = gig.institution.user_id
    db.close()

    # First, express interest
    db = SessionLocal()
    interest = GigInterest(job_id=gig_id, professional_id=professional.id)
    db.add(interest)
    db.commit()
    db.close()

    response = test_client.post(f'/api/jobs/{gig_id}/cancel-interest', headers={'Authorization': f'Bearer {professional_token}'})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Interest canceled successfully'
    db = SessionLocal()
    assert db.query(GigInterest).count() == 0
    db.close()
    mock_socketio.emit.assert_called_with('notification', {'message': 'The professional has withdrawn their interest in this gig.'}, room=f'user_{institution_user_id}')

@patch('app.socketio')
def test_institution_delete_gig(mock_socketio, test_client, init_database):
    institution_token = get_auth_token(test_client, 'institution@test.com', 'password')
    db = SessionLocal()
    gig = db.query(Job).first()
    gig_id = gig.id
    gig_title = gig.title
    professional = db.query(Professional).filter_by(full_name='John Doe').first()
    professional_user_id = professional.user_id
    interest = GigInterest(job_id=gig.id, professional_id=professional.id)
    db.add(interest)
    db.commit()
    db.close()

    response = test_client.delete(f'/api/jobs/{gig_id}', headers={'Authorization': f'Bearer {institution_token}'})

    assert response.status_code == 200
    assert response.get_json()['message'] == 'Gig deleted successfully'
    db = SessionLocal()
    assert db.query(Job).count() == 0
    assert db.query(GigInterest).count() == 0
    db.close()
    mock_socketio.emit.assert_called_with('notification', {'message': f'The gig "{gig_title}" is no longer available.'}, room=f'user_{professional_user_id}')

def test_unauthorized_access(test_client, init_database):
    professional_token = get_auth_token(test_client, 'professional@test.com', 'password')
    institution_token = get_auth_token(test_client, 'institution@test.com', 'password')
    db = SessionLocal()
    gig = db.query(Job).first()
    db.close()

    # Professional tries to close a gig
    response = test_client.post(f'/api/jobs/{gig.id}/close', headers={'Authorization': f'Bearer {professional_token}'})
    assert response.status_code == 403

    # Professional tries to delete a gig
    response = test_client.delete(f'/api/jobs/{gig.id}', headers={'Authorization': f'Bearer {professional_token}'})
    assert response.status_code == 403

    # Institution tries to cancel interest
    response = test_client.post(f'/api/jobs/{gig.id}/cancel-interest', headers={'Authorization': f'Bearer {institution_token}'})
    assert response.status_code == 403
