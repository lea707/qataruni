from models import *
from sqlalchemy.orm import configure_mappers

def test_model_mapping_initializes():
    configure_mappers()
    assert True