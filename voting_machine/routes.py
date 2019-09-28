from flask import render_template, request, redirect, url_for
from voting_machine import app, db
from voting_machine.models import Vote
from voting_machine.forms import VoteForm
import requests

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
	return render_template('vote.html', form=form, election=election, candidates=candidates)

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

def get_election(election_id):
	response = 0
	try:
		response = requests.get('http://localhost:5000/get_election/?election='+str(election_id))
		data = response.json()
		print(data)
	except requests.exceptions.RequestException as e:
		print(e)
	return data['election'], data['candidates']