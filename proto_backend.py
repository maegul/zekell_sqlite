import sys
import string
import random
import json

import flask
from flask import Flask, request, jsonify

import zekell as zkl

def lp(msg):
	print(msg, file=sys.stdout)

def hack_cors(resp_content):

	resp = flask.make_response(
			resp_content
			# {'a': 1, 'b': 2},  # response
		)
	# unsafe!!??
	resp.headers['Access-Control-Allow-Origin'] = '*'

	return resp

app = Flask(__name__)

USE_ROW_OBJ = True
new_db = lambda : zkl.db_connection(zkl.ZK_DB_PATH, use_row_obj=USE_ROW_OBJ)

# domain from which requests will be made (port necessary?)
ORIGIN = 'http://localhost:8000'


# # ALLOW CORS: After Request hook to allow CORS

@app.after_request
def apply_CORS_headers(response: flask.Response):

	response.headers['Access-Control-Allow-Origin'] = ORIGIN
	response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

	return response


@app.route("/test")
def hello_world():
	return "<p>Hello, World!</p>"


@app.route("/jsontest")
def jsontest():
	resp_content = {'content': ''.join(random.choices(string.ascii_letters, k=10))}
	resp = flask.make_response(
			resp_content
			# {'a': 1, 'b': 2},  # response
		)
	# unsafe!!??
	resp.headers['Access-Control-Allow-Origin'] = '*'

	# resp.headers['crossorigin'] = 'anonymous'
	# lp(resp.headers)

	return resp

# @app.route('/echo_query', methods='GET')
@app.get('/echo_query')
def echo_query():
	v = request.args

	return (
			f'Parameter is: {[(k,v) for k,v in v.items()]}',
			# status code
			200
		)
	# v = request.args.get('test')
	# return f'Parameter is: {v}'



# # General "q" search

@app.get('/note')
def get_note_by_id():
	note_id = request.args.get('id')

	if not note_id:
		return (
				json.dumps({'error': 'Must provide note id'}),
				400
			)
	try:
		note_id_int = int(note_id)
	except ValueError:
		return (
				json.dumps({'error': 'note id invalid'}),
				400
			)

	db = new_db()
	note_data = zkl.get_note_text_from_id(db, note_id_int)

	return json.dumps(dict(note_data[0]))


@app.post('/general_search')
def general_search():
	# v = request.args
	# query = v.get('q', type=str)

	# if not query:
	# 	return 'Must provide search query', 400

	# return query

	# data = request.get_json()
	content_type = request.headers.get('Content-Type')

	if not content_type:
		return (
				json.dumps({'error': 'Must provide a content type for a search'}),
				400
			)

	# only two post content-types I know about
	if content_type == "application/json":
		data = request.get_json()
	elif (
			('multipart/form-data' in content_type)  # multipart often contains a boundary spec
			or
			('application/x-www-form-urlencoded' == content_type)
		):
		data = request.form
	else:
		return (
				json.dumps({'error': 'Content-type inappropriate for search'}),
				400
			)

	query = data.get('query')
	if not query:
		return (
				json.dumps({'error': 'Must provide a query'}),
				400
			)

	db = new_db()
	full_query = zkl.mk_super_query(query)
	results = zkl.convert_rows_to_dicts(db.ex(full_query))

	json_results = json.dumps(results)

	return json_results





# # MAIN

if __name__ == '__main__':
	app.run(debug=True)
