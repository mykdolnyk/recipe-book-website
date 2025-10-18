SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"

PASSWORD_POLICY = {
    'length': 8, 
    'uppercase': 1,
    'numbers': 1,  
    'special': 1,  
    'nonletters': 1,
    'entropybits': 20,
    'strength': 0.66,
}
