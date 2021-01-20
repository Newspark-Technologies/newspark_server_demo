from app import application
# from werkzeug.contrib.profiler import ProfilerMiddleware
# app.config['PROFILE'] = True
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
application.run(threaded=True, debug=True)
# app.run(host='0.0.0.0', port=5000, threaded=True, debug=True, use_reloader=False)
