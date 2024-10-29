from flask import Flask, request, jsonify
from celery import Celery, Task
from tasks import add_together  # Import the task function here

# Initialize Flask app
app = Flask(__name__)

# Configure Celery with Flask settings
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://redis:6379",       # Redis broker URL within Docker
        result_backend="redis://redis:6379",   # Redis backend
        task_ignore_result=True                # Ignore results by default
    )
)

# Function to create a Celery app within Flask
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        # Ensure Celery runs with Flask's application context
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

# Initialize Celery
celery_app = celery_init_app(app)

@app.route("/add", methods=["POST"])
def start_add():
    a = request.form.get("a", type=int)
    b = request.form.get("b", type=int)
    
    if a is None or b is None:
        return jsonify({"error": "Both 'a' and 'b' parameters are required"}), 400
    
    result = add_together.delay(a, b)  # Run task in background
    return jsonify({"result_id": result.id})

@app.route("/result/<id>")
def task_result(id):
    from celery.result import AsyncResult
    result = AsyncResult(id)
    return {
        "ready": result.ready(),           
        "successful": result.successful(), 
        "value": result.result if result.ready() else None  
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
