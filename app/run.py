from app_factory import create_app
import config

app = create_app(config_object=config)

if __name__ == "__main__":
    app.run('0.0.0.0', debug=True)