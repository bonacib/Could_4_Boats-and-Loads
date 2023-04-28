from flask import Flask, request
import lodging
import guest

app = Flask(__name__)
app.register_blueprint(lodging.bp)
app.register_blueprint(guest.bp)

@app.route('/')
def index():
    return "Please navigate to /lodgings to use this API"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)