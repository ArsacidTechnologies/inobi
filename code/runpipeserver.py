

from ping_pipe import make_app


if __name__ == '__main__':
    make_app().run(host='0.0.0.0', port=4500, debug=True)
