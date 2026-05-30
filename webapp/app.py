from waitress import serve

from webapp import create_app

app = create_app()

if __name__ == "__main__":
    # logging.getLogger('waitress').setLevel(logging.ERROR)
    # serve(app, host="0.0.0.0", port=8080)
    app.run(host="0.0.0.0", port=8080, debug=True)
