from sqlalchemy.orm import Session
from ..model.identity_model import Identity
from ..security.password.password import verify_password


class AuthenticationRepository:

    def __init__ (self, db : Session):
        self.db = db

################################################
    # authentication process #
################################################

    def get_by_email(self, email : str) -> Identity:
        return self.db.query(Identity).filter(Identity.email==email)


#################################################
        # registration process #
#################################################

    def create_identity(self, email : str, hashed_password : str) -> Identity:
        new_identity = Identity(
            email = email,
            hashed_password = hashed_password
        )
        self.db.add(new_identity)
        self.db.commit()
        self.db.refresh(new_identity)
        return new_identity
