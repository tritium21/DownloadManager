from aiohttp import web
from aiohttp_jinja2 import setup as jinja2_setup
from jinja2 import PackageLoader, pass_context

from .views import routes, sse_worker
from .events import install_events
from .download import Manager


def url_rewriter(env, prefix=None):
    url_for = env.globals['url']
    if prefix is None:
        return url_for
    @pass_context
    def _url_for(*args, **kwargs):
        url = url_for(*args, **kwargs)
        return url.with_path(f'{prefix}{url.path}')
    env.globals['url'] = _url_for
    return _url_for


def route_rewriter(routes, prefix=None):
    if prefix is None:
        return routes
    newroutes = []
    for item in routes:
        if isinstance(item, web.RouteDef):
            newroutes.append(web.RouteDef(
                method=item.method,
                path=f'{prefix}{item.path}',
                handler=item.handler,
                kwargs=item.kwargs
            ))
        elif isinstance(item, web.StaticDef):
            newroutes.append(web.StaticDef(
                prefix=f'{prefix}{item.prefix}',
                path=item.path,
                kwargs=item.kwargs,
            ))
    return newroutes


def init(config):
    app = web.Application()
    app['config'] = config
    man = Manager.install(app)
    env = jinja2_setup(
        app,
        loader=PackageLoader(__package__),
        extensions=["jinja2_humanize_extension.HumanizeExtension"],
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals['global_title'] = config.name
    url_rewriter(env, prefix=config.url_prefix)
    app.add_routes(route_rewriter(routes, prefix=config.route_prefix))
    install_events(app, sse_worker)
    return app