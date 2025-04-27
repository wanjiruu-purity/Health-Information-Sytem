from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/health_system'  # Change this if necessary
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Program model
class Program(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Program {self.name}>"

# Define the Client model
class Client(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    programs = db.relationship('Program', secondary='client_program', backref='clients')

    def __repr__(self):
        return f"<Client {self.name}>"

# Define the association table between Client and Program
class ClientProgram(db.Model):
    __tablename__ = 'client_program'
    client_id = db.Column(db.String(10), db.ForeignKey('client.id'), primary_key=True)
    program_id = db.Column(db.String(10), db.ForeignKey('program.id'), primary_key=True)

# Function to validate program IDs
def validate_program_ids(program_ids):
    if not isinstance(program_ids, list) or not all(isinstance(id, str) for id in program_ids):
        abort(400, 'Program IDs must be a list of strings.')

# Function to validate client data
def validate_client_data(data):
    if 'id' not in data or 'name' not in data or 'age' not in data:
        abort(400, 'Missing required client fields: id, name, and age.')
    if not isinstance(data['age'], int):
        abort(400, 'Age must be an integer.')

# Initialize the database tables 
def create_tables():
    with app.app_context():
        db.create_all()

create_tables()

# Route to create a new program
@app.route('/programs', methods=['POST'])
def create_program():
    data = request.get_json()
    if not data.get('id') or not data.get('name'):
        abort(400, 'Missing required fields: id and name.')
    program = Program(id=data['id'], name=data['name'])
    db.session.add(program)
    db.session.commit()
    return jsonify({'message': 'Program created successfully'}), 201

# Route to create a new client
@app.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    validate_client_data(data)
    client = Client(id=data['id'], name=data['name'], age=data['age'])
    db.session.add(client)
    db.session.commit()
    return jsonify({'message': 'Client created successfully'}), 201

# Route to enroll a client in one or more programs
@app.route('/clients/<client_id>/enroll', methods=['POST'])
def enroll_client(client_id):
    data = request.get_json()
    if not data:
        abort(400, 'Invalid or missing JSON payload.')

    validate_program_ids(data.get('program_ids', []))
    
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'message': 'Client not found'}), 404

    programs = Program.query.filter(Program.id.in_(data['program_ids'])).all()
    if not programs:
        return jsonify({'message': 'Programs not found'}), 404

    client.programs.extend(programs)
    db.session.commit()
    return jsonify({'message': 'Client enrolled in programs successfully'}), 200

# Route to view a client profile
@app.route('/clients/<client_id>', methods=['GET'])
def view_client_profile(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'message': 'Client not found'}), 404

    programs = [{"id": program.id, "name": program.name} for program in client.programs]
    return jsonify({
        'id': client.id,
        'name': client.name,
        'age': client.age,
        'enrolled_programs': programs
    })

if __name__ == '__main__':
    app.run(debug=True)
