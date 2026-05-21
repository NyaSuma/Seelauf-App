from flask import Flask, render_template, request
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/user_interface')
def user_interface():
    return render_template('user_interface.html') 







if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

