from flask import render_template, request, redirect, url_for, jsonify, make_response, flash
from voting_machine import app, db
from voting_machine.models import Vote, Fingerprint
from voting_machine.forms import VoteForm
import requests
import secrets
from collections import defaultdict
import json
import pdfkit
import gmpy2

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/vote/", methods=['GET', 'POST'])
def vote():
	voter_id = int(request.form.get("voter"))
	election_id = int(request.form.get("election"))
	authentication_token = request.form.get("authentication_token")
	if not voter_is_valid(authentication_token, election_id, voter_id):
		return redirect(url_for('home'))
	election, candidates = get_election(election_id)
	form = VoteForm()
	form.vote.choices = [(candidate['id'], candidate['email']) for candidate in candidates]
	if (request.form.get("votes")):
		votes_data = json.loads(request.form.get("votes"))
		votes = votes_data["votes"]
		tally_proof = votes_data["tally_proof"]
		#print(votes)
		#vote_value = 0
		#vote_values = {}
		f = secrets.token_hex(32)
		fingerprint = Fingerprint(voter_id=voter_id, fingerprint=f)
		db.session.add(fingerprint)
		db.session.flush()
		db.session.refresh(fingerprint)

		ciphertext_ax = 1;
		n = int(election['pub_key'])
		n_sq = n * n

		vote_error = False
		for vote in votes:
			candidate_id = int(vote['id'])
			vote_inst = Vote(fingerprint_id=fingerprint.id, election_id=election_id, candidate_id=candidate_id, ciphertext=vote['ciphertext'])
			if (verify_vote(n, vote['proof'], int(vote['ciphertext']))):
				db.session.add(vote_inst)
				ciphertext_ax = ciphertext_ax * int(vote['ciphertext']) % n_sq
			else:
				vote_error = True
				break

		# Calculate tally is in range [0, 1]
		if not vote_error:
			if not verify_vote(n, tally_proof, int(ciphertext_ax)):
				vote_error = True

		#for candidate in candidates:
		#	if int(candidate['id']) == int(vote):
		#		vote_value = 1
		#	else:
		#		vote_value = 0
		#	vote_values[candidate['id']] = {'candidate': candidate['email'], 'value': vote_value}
		#	vote_inst = Vote(fingerprint_id=fingerprint.id, election_id=election_id, candidate_id=candidate['id'], ciphertext=vote_value, nonce=0)
		#	db.session.add(vote_inst)
		if (not vote_error):
			db.session.commit()
			tell_voter_voted(voter_id=voter_id, authentication_token=authentication_token)

			rendered = render_template('vote_receipt.html', fingerprint=fingerprint, votes=votes, candidates=candidates, election_id=election_id)
			pdf = pdfkit.from_string(rendered, False)
			response = make_response(pdf)
			response.headers['Content-Type'] = 'application/pdf'
			response.headers['Content-Disposition'] = 'inline; filename='+str(election['title'])+' - Receipt.pdf'
			return response;
		else:
			flash("Vote is not valid, please try again", "danger")
			return render_template('vote.html', form=form, election=election, candidates=candidates, authentication_token=authentication_token, voter_id=voter_id, election_id=election_id)
		#return render_template('vote_success.html', fingerprint=fingerprint, votes=votes, candidates=candidates, election_id=election_id)
	else:
		return render_template('vote.html', form=form, election=election, candidates=candidates, authentication_token=authentication_token, voter_id=voter_id, election_id=election_id)

def getInverse(m, n):
	return gmpy2.invert(m, n);

def verify_vote(n, proof, C):
	g = n + 1
	c1 = int(proof['c1'])
	c2 = int(proof['c2'])
	t1num = int(proof['t1num'])
	t1den = int(proof['t1den'])
	t2num = int(proof['t2num'])
	t2den = int(proof['t2den'])
	s1 = int(proof['s1'])
	s2 = int(proof['s2'])

	n_sq = n * n
	c_g = (C * getInverse(g, n_sq)) % n_sq

	if (t2den == 1):
		s2_n = pow(s2, n, n_sq)
		s2_n_calc = ((pow(c2, n, n_sq) * pow(C, (c2 * n), n_sq) % n_sq) * t2num) % n_sq
	else:
		s2_n = float(pow(s2, n, n_sq))
		s2_n_calc = ((pow(c2, n, n_sq) * pow(C, (c2 * n), n_sq) % n_sq) * t2num / t2den) % n_sq

	if t1den == 1:
		s1_n = pow(s1, n, n_sq)
		s1_n_calc = (((pow(c1, n, n_sq) * pow(c_g, (c1 * n), n_sq)) % n_sq) * t1num) % n_sq
	else:
		s1_n = float(pow(s1, n, n_sq))
		s1_n_calc = (((pow(c1, n, n_sq) * pow(c_g, (c1 * n), n_sq)) % n_sq) * t1num / t1den) % n_sq

	if (round(s1_n) == round(s1_n_calc) and round(s2_n) == round(s2_n_calc)):
		return True
	return False

@app.route("/get_votes/", methods=['GET', 'POST'])
def get_votes():
	data_dict = {'votes': defaultdict(dict)}
	if request.remote_addr != "127.0.0.1":
		return jsonify({})
	election_id = int(request.args.get("election_id"))
	votes = db.session.query(Vote, Fingerprint).filter_by(election_id=election_id).join(Fingerprint, Vote.fingerprint_id == Fingerprint.id).all()
	for vote in votes:
		data_dict['votes'][vote.Fingerprint.fingerprint][vote.Vote.candidate_id] = vote.Vote.ciphertext
	return jsonify(data_dict)


def voter_is_valid(authentication_token, election_id, voter_id):
	response = 0
	status = False
	try:
		response = requests.get('http://localhost:5000/vm_check/?election='+str(election_id)+"&voter="+str(voter_id)+"&authentication_token="+str(authentication_token))
		data = response.json()
		status = data['status']
	except requests.exceptions.RequestException as e:
		print(e)
	return status

def tell_voter_voted(voter_id, authentication_token):
	status = False
	try:
		response = requests.get('http://localhost:5000/voter_voted/?voter_id='+str(voter_id)+"&authentication_token="+str(authentication_token))
		data = response.json()
		status = data['status']
	except requests.exceptions.RequestException as e:
		print(e)
	return status

def get_election(election_id):
	response = 0
	try:
		response = requests.get('http://localhost:5000/get_election/?election='+str(election_id))
		data = response.json()
	except requests.exceptions.RequestException as e:
		print(e)
	return data['election'], data['candidates']