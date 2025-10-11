from app_factory import create_app


app = create_app(config_object=object)

if __name__ == "__main__":
    app.run('0.0.0.0', debug=True)