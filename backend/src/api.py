import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# GETs all drinks

@app.route('/drinks', methods=['GET'])
def get_drinks():
    drink_selection = Drink.query.all()
    drinks = []

    for drink in drink_selection:
        drinks.append(drink.short())

    return jsonify({
        'success': True,
        'drinks': drinks
    })

# GETs drink details and requires the 'get:drinks-detail' permission

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = []

    try:
        drink_selection = Drink.query.all()

        for drink in drink_selection:
            drinks.append(drink.long())

        return jsonify(
            {"success": True,
            "drinks": drinks
        })

    except Exception as e:
        abort(404)

# POSTs new drinks and requires the 'post:drinks' permission

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(jwt):
    body = request.get_json()
    title = body['title']
    recipe = body['recipe']
    drink = Drink(title=title, recipe=json.dumps(recipe))

    try:
        drink.insert()
    except Exception as e:
        print('ERROR: ', str(e))
        abort(422)

    return jsonify({
        "success": True,
        "drinks": drink.long()
    })

# Edits existing drinks and requires the 'patch:drinks' permission

@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):

    drink_selection = Drink.query.get(id)
    response = request.get_json()

    if not drink_selection:
        abort(404)

    try:
        drink_selection.title = response['title']

        if 'recipe' in response:
            drink_selection.recipe = json.dumps(response['recipe'])

        drink_selection.update()

    except Exception as e:
        abort(401)
        print('Exception :', e)

    return jsonify({
        "success": True,
        "drinks": [drink_selection.long()]
    })

# Deletes drinks and requires the 'delete:drinks' permissions

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(*args, **kwargs):
    id = kwargs['id']
    drink = Drink.query.filter_by(id=id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except Exception as e:
        print('EXCEPTION: ', str(e))
        abort(500)

    return jsonify({
        'success': True,
        'delete': id
    })

## Errors Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def notfound(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'not found',
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'Bad request',
    }), 400


@app.errorhandler(AuthError)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': error.error['description'],
    }), 401
