from voting_machine import db

class Vote(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	voter_id = db.Column(db.Integer, nullable=False)
	ciphertext = db.Column(db.String(120), nullable=False)
	nonce = db.Column(db.Integer, nullable=False)
	fingerprint = db.Column(db.String(120), nullable=False)

	def __repr__(self):
		return f"Vote:('{self.fingerprint}', '{self.ciphertext}')"