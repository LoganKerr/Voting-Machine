from voting_machine import db

class Fingerprint(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	voter_id = db.Column(db.Integer, nullable=False)
	fingerprint = db.Column(db.String(64), nullable=False)
	votes = db.relationship('Vote', backref='fingerprint', lazy=True)

	def __repr__(self):
		return f"Fingerprint:('{self.voter_id}','{self.fingerprint}')"

class Vote(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	fingerprint_id = db.Column(db.Integer, db.ForeignKey('fingerprint.id'), nullable=False)
	election_id = db.Column(db.Integer, nullable=False)
	candidate_id = db.Column(db.Integer, nullable=False)
	ciphertext = db.Column(db.String(2048), nullable=False)
	nonce = db.Column(db.String(2048), nullable=False)

	def __repr__(self):
		return f"Vote:('{self.election_id}','{self.fingerprint_id}', '{self.ciphertext}', '{self.nonce}')"