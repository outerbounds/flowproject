import time

from metaflow import project, FlowSpec, config_expr, Config, current
from metaflow.cards import Markdown

try:
    # Python > 3.10
    import tomllib

    toml_parser = "tomllib.loads"
except ImportError:
    # Python < 3.10
    # pip install toml
    toml_parser = "toml.loads"


class BaseFlow(FlowSpec):
    flowconfig = Config("flowconfig", default="flowproject.toml", parser=toml_parser)

    @property
    def sensor_value(self):
        try:
            return current.trigger.run.data.value
        except:
            pass

    def query_snowflake(self, sql=None, template=None, card=False):
        if card and hasattr(current, 'card'):
            def _out(txt):
                current.card.append(Markdown(txt))
        else:
            def _out(txt):
                pass

        if template:
            if isinstance(template, tuple):
                fname, args = template
            else:
                fname = template
                args = None

            with open(f'sql/{fname}.sql') as f:
                sql = (f.read(), args) if args else f.read()
        
        _out(f"## 🛢️ Executing SQL")
        _out(f"{sql}")
        
        from metaflow import Snowflake
        with Snowflake(integration=self.flowconfig.data.integration) as cn:
            with cn.cursor() as cur:
                t = time.time()
                if isinstance(sql, tuple):
                    cur.execute(*sql)
                else:
                    cur.execute(sql)
                secs = int(1000 * (time.time() - t))
                _out(f"Query finished in {secs}ms")
                return list(cur.fetchall())
